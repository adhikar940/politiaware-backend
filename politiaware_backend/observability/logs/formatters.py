"""
Trace-Correlated JSON Formatter for OpenSearch and Structured Logging.
Extracts OpenTelemetry trace_id and span_id to link logs directly to Jaeger traces.
"""

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Dict

from ..config import config


def _get_trace_context():
    """Retrieves current trace_id and span_id if an active span exists."""
    try:
        from opentelemetry import trace
        current_span = trace.get_current_span()
        context = current_span.get_span_context()
        if context and context.is_valid:
            return f"{context.trace_id:032x}", f"{context.span_id:016x}"
    except Exception:
        pass
    return None, None


class OpenSearchJSONFormatter(logging.Formatter):
    """
    Formats standard library LogRecords into OpenSearch-compatible JSON documents,
    automatically enriched with W3C trace_id and span_id.
    """

    def __init__(self, service_name: str = None, environment: str = None, **kwargs):
        super().__init__(**kwargs)
        self.service_name = service_name or config.service_name
        self.environment = environment or config.environment

    def format(self, record: logging.LogRecord) -> str:
        # Standard timestamp in ISO 8601 with milliseconds and UTC offset
        record_time = datetime.fromtimestamp(record.created, tz=timezone.utc)
        iso_time = record_time.isoformat()

        # 1. Retrieve OpenTelemetry Trace & Span ID
        # Check record attributes first (set by LoggingInstrumentor)
        trace_id = getattr(record, "otelTraceID", None)
        span_id = getattr(record, "otelSpanID", None)

        if not trace_id or trace_id == "00000000000000000000000000000000":
            # Check active span directly
            ctx_trace_id, ctx_span_id = _get_trace_context()
            if ctx_trace_id:
                trace_id = ctx_trace_id
                span_id = ctx_span_id

        # 2. Build structured document
        log_entry: Dict[str, Any] = {
            "@timestamp": iso_time,
            "service": {
                "name": self.service_name,
                "version": config.service_version,
                "environment": self.environment,
            },
            "log": {
                "level": record.levelname,
                "logger": record.name,
                "origin": {
                    "file": record.filename,
                    "line": record.lineno,
                    "function": record.funcName,
                },
            },
            "process": {
                "pid": record.process,
                "thread_name": record.threadName,
            },
            "message": record.getMessage(),
        }

        # 3. Add trace correlation
        if trace_id:
            log_entry["trace_id"] = trace_id
        if span_id:
            log_entry["span_id"] = span_id

        # 4. Add exception details if present
        if record.exc_info:
            log_entry["error"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Exception",
                "message": str(record.exc_info[1]),
                "stack_trace": traceback.format_exception(*record.exc_info),
            }

        # 5. Extract extra custom fields attached to log record
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "asctime", "otelTraceID", "otelSpanID",
            "otelTraceSampled", "otelServiceName",
        }
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith("_")
        }
        if extras:
            log_entry["extra"] = extras

        return json.dumps(log_entry, default=str)
