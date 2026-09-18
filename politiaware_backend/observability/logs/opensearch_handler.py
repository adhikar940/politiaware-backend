"""
Asynchronous, Non-Blocking OpenSearch Log Handler.
Streams structured JSON logs with trace correlation to OpenSearch (port 9200).
Uses an internal queue and background daemon worker to ensure zero request-path latency.
"""

import atexit
import json
import logging
import queue
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import List, Optional

from ..config import config
from .formatters import OpenSearchJSONFormatter

_SHUTDOWN_SENTINEL = object()


class OpenSearchHandler(logging.Handler):
    """
    Buffered, asynchronous logging handler that indexes log documents directly
    into OpenSearch via REST API (_bulk or _doc).
    """

    def __init__(
        self,
        opensearch_url: Optional[str] = None,
        index_prefix: Optional[str] = None,
        buffer_size: Optional[int] = None,
        flush_interval: Optional[float] = None,
        level: int = logging.NOTSET,
    ):
        super().__init__(level=level)
        self.opensearch_url = (opensearch_url or config.opensearch_url).rstrip("/")
        self.index_prefix = index_prefix or config.opensearch_index_prefix
        self.buffer_size = buffer_size or config.opensearch_buffer_size
        self.flush_interval = flush_interval or config.opensearch_flush_interval

        # Default formatter if none provided
        if not self.formatter:
            self.setFormatter(OpenSearchJSONFormatter())

        # Queue and background worker thread
        self.queue: queue.Queue = queue.Queue(maxsize=10000)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="OpenSearchLogWorker",
        )
        self._worker_thread.start()

        # Register clean shutdown on Python exit
        atexit.register(self.close)

    def emit(self, record: logging.LogRecord):
        """Pushes formatted log string onto the queue (non-blocking)."""
        # Prevent self-logging loops from OpenSearch handler or urllib
        if record.name.startswith("observability.logging.opensearch") or "urllib" in record.name:
            return

        try:
            msg = self.format(record)
            self.queue.put_nowait(msg)
        except queue.Full:
            # Under extreme load, drop oldest to avoid memory exhaustion
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(msg)
            except Exception:
                pass
        except Exception:
            self.handleError(record)

    def _worker_loop(self):
        """Worker thread loop: collects log entries and flushes in batches."""
        batch: List[str] = []
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                # Wait for items up to 0.5s
                timeout = max(0.1, min(0.5, self.flush_interval - (time.time() - last_flush)))
                item = self.queue.get(timeout=timeout)

                if item is _SHUTDOWN_SENTINEL:
                    break

                batch.append(item)

                # Flush if buffer is full or timeout expired
                now = time.time()
                if len(batch) >= self.buffer_size or (batch and now - last_flush >= self.flush_interval):
                    self._send_bulk(batch)
                    batch = []
                    last_flush = now

            except queue.Empty:
                # Flush remaining items if time elapsed
                if batch and time.time() - last_flush >= self.flush_interval:
                    self._send_bulk(batch)
                    batch = []
                    last_flush = time.time()

        # Final drain on shutdown
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                if item is not _SHUTDOWN_SENTINEL:
                    batch.append(item)
            except queue.Empty:
                break
        if batch:
            self._send_bulk(batch)

    def _get_current_index_name(self) -> str:
        """Returns time-partitioned index name, e.g. politiaware-logs-2026.09.17"""
        today_str = datetime.now(timezone.utc).strftime("%Y.%m.%d")
        return f"{self.index_prefix}-{today_str}"

    def _send_bulk(self, items: List[str]):
        """Sends a batch of JSON documents to OpenSearch using the bulk API."""
        if not items or not config.opensearch_logging_enabled:
            return

        index_name = self._get_current_index_name()
        bulk_endpoint = f"{self.opensearch_url}/{index_name}/_bulk"

        # Build NDJSON payload:
        # {"index": {}}
        # {document}
        payload_parts = []
        for item in items:
            payload_parts.append('{"index": {}}\n')
            payload_parts.append(item)
            payload_parts.append('\n')

        data = "".join(payload_parts).encode("utf-8")
        headers = {
            "Content-Type": "application/x-ndjson",
            "User-Agent": "Politiaware-OpenSearch-Logger/1.0",
        }

        try:
            req = urllib.request.Request(bulk_endpoint, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status not in (200, 201):
                    # Silently ignore or handle non-200
                    pass
        except urllib.error.URLError:
            # OpenSearch temporarily down or unreachable; drop batch gracefully
            pass
        except Exception:
            pass

    def close(self):
        """Shuts down worker thread cleanly."""
        if not self._stop_event.is_set():
            self._stop_event.set()
            try:
                self.queue.put_nowait(_SHUTDOWN_SENTINEL)
            except Exception:
                pass
            if self._worker_thread.is_alive():
                self._worker_thread.join(timeout=2.0)
        super().close()
