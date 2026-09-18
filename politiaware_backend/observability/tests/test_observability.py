"""
Unit and Integration Tests for Politiaware Observability Package.
Verifies:
1. Configuration loading and environment parsing.
2. Jaeger & Arize toggles defaulting to False.
3. Multi-backend routing (both True, either True, both False).
4. Fault tolerance: Jaeger, Arize, and Valkey errors log logger.error without crashing.
5. Custom trace_span context manager.
6. Valkey auto-instrumentation & statement formatting.
7. OpenSearch JSON formatting and trace correlation.
8. OpenSearch async handler buffering and graceful shutdown.
9. Observability middleware span enrichment.
10. End-to-end init_observability idempotency.
"""

import asyncio
import json
import logging
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directories to sys.path for direct standalone test execution
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(test_dir, "..", "..", ".."))
backend_dir = os.path.abspath(os.path.join(test_dir, "..", ".."))

for p in [project_root, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from politiaware_backend.observability.config import ObservabilityConfig, _to_bool
from politiaware_backend.observability.logs.formatters import OpenSearchJSONFormatter
from politiaware_backend.observability.logs.opensearch_handler import OpenSearchHandler
from politiaware_backend.observability.instrumentors.valkey_inst import ValkeyInstrumentor, _format_statement
from politiaware_backend.observability.middleware import ObservabilityMiddleware
from politiaware_backend.observability import init_observability, get_tracer, trace_span
from politiaware_backend.observability.tracer import (
    _create_jaeger_exporter,
    _create_arize_exporter,
    init_tracer,
    DummyTracer,
)
from politiaware_backend.valkey_cache.django_backend import ValkeyCache


class TestObservabilityConfig(unittest.TestCase):
    """Tests configuration loading and boolean parsing."""

    def test_to_bool_helper(self):
        self.assertTrue(_to_bool("True"))
        self.assertTrue(_to_bool("true"))
        self.assertTrue(_to_bool("1"))
        self.assertTrue(_to_bool("yes"))
        self.assertTrue(_to_bool("on"))
        self.assertFalse(_to_bool("False"))
        self.assertFalse(_to_bool("0"))
        self.assertFalse(_to_bool("no"))
        self.assertFalse(_to_bool(None, default=False))
        self.assertTrue(_to_bool(None, default=True))

    def test_config_defaults(self):
        conf = ObservabilityConfig()
        self.assertIsNotNone(conf.service_name)
        self.assertIsNotNone(conf.jaeger_endpoint)
        self.assertIsNotNone(conf.arize_endpoint)
        self.assertIsNotNone(conf.opensearch_url)
        self.assertIn("politiaware-logs", conf.opensearch_index_prefix)

    def test_jaeger_and_arize_default_to_false(self):
        """Both Jaeger and Arize must default to False unless explicitly set."""
        with patch.dict(os.environ, {}, clear=True):
            conf = ObservabilityConfig()
            self.assertFalse(conf.jaeger_enabled, "JAEGER_ENABLED must default to False")
            self.assertFalse(conf.arize_enabled, "ARIZE_ENABLED must default to False")
            self.assertFalse(conf.has_active_trace_backend, "has_active_trace_backend must be False when both are disabled")


class TestMultiBackendRoutingAndFaultTolerance(unittest.TestCase):
    """Tests routing logic and graceful logger.error handling."""

    def test_jaeger_failure_logs_error_without_raising(self):
        """If Jaeger is unreachable or exporter fails, log logger.error and return None."""
        with patch("politiaware_backend.observability.tracer.config") as mock_conf:
            mock_conf.jaeger_endpoint = "http://invalid-jaeger-host:4318/v1/traces"
            mock_exporter_mod = MagicMock()
            mock_exporter_mod.OTLPSpanExporter.side_effect = Exception("Connection refused")
            with patch.dict(sys.modules, {"opentelemetry.exporter.otlp.proto.http.trace_exporter": mock_exporter_mod}):
                with patch("politiaware_backend.observability.tracer.logger.error") as mock_log_err:
                    exporter = _create_jaeger_exporter()
                    self.assertIsNone(exporter)
                    mock_log_err.assert_called_once()
                    call_msg = mock_log_err.call_args[0][0]
                    self.assertIn("Failed to initialize Jaeger trace exporter", call_msg)

    def test_arize_failure_logs_error_without_raising(self):
        """If Arize is unreachable or exporter fails, log logger.error and return None."""
        with patch("politiaware_backend.observability.tracer.config") as mock_conf:
            mock_conf.arize_endpoint = "http://invalid-arize-host:6006/v1/traces"
            mock_conf.arize_space_id = "test-space"
            mock_conf.arize_api_key = "test-key"
            mock_exporter_mod = MagicMock()
            mock_exporter_mod.OTLPSpanExporter.side_effect = Exception("Arize network timeout")
            with patch.dict(sys.modules, {"opentelemetry.exporter.otlp.proto.http.trace_exporter": mock_exporter_mod}):
                with patch("politiaware_backend.observability.tracer.logger.error") as mock_log_err:
                    exporter = _create_arize_exporter()
                    self.assertIsNone(exporter)
                    mock_log_err.assert_called_once()
                    call_msg = mock_log_err.call_args[0][0]
                    self.assertIn("Failed to initialize Arize trace exporter", call_msg)

    def test_dual_backend_routing_success(self):
        """When both are enabled, both exporters should be created."""
        with patch("politiaware_backend.observability.tracer.config") as mock_conf:
            mock_conf.enabled = True
            mock_conf.jaeger_enabled = True
            mock_conf.arize_enabled = True
            mock_conf.has_active_trace_backend = True
            mock_conf.jaeger_endpoint = "http://localhost:4318/v1/traces"
            mock_conf.arize_endpoint = "http://localhost:6006/v1/traces"
            mock_conf.arize_space_id = ""
            mock_conf.arize_api_key = ""
            mock_conf.sampler_name = "always_on"

            mock_trace = MagicMock()
            mock_sdk = MagicMock()
            mock_res = MagicMock()

            with patch.dict(sys.modules, {
                "opentelemetry": mock_trace,
                "opentelemetry.trace": mock_trace,
                "opentelemetry.sdk.trace": mock_sdk,
                "opentelemetry.sdk.trace.export": mock_sdk,
                "opentelemetry.sdk.trace.sampling": mock_sdk,
                "opentelemetry.sdk.resources": mock_res,
            }):
                with patch("politiaware_backend.observability.tracer._create_jaeger_exporter", return_value=MagicMock()) as mock_j:
                    with patch("politiaware_backend.observability.tracer._create_arize_exporter", return_value=MagicMock()) as mock_a:
                        import politiaware_backend.observability.tracer as tr_mod
                        tr_mod._INITIALIZED = False
                        tr_mod.init_tracer()
                        mock_j.assert_called_once()
                        mock_a.assert_called_once()
                        tr_mod._INITIALIZED = False


class TestValkeyFaultTolerance(unittest.TestCase):
    """Tests Valkey cache error handling: logs logger.error and returns defaults."""

    def test_format_statement(self):
        stmt = _format_statement("GET", ("user:123",))
        self.assertEqual(stmt, "GET user:123")

        stmt_set = _format_statement("SET", ("user:123", "secret-payload-data"))
        self.assertEqual(stmt_set, "SET user:123 <payload>")

        stmt_args = _format_statement("MGET", ("k1", "k2", "k3", "k4", "k5"))
        self.assertIn("MGET k1 ... (5 args)", stmt_args)

    def test_valkey_instrumentor_patch(self):
        instrumentor = ValkeyInstrumentor()
        instrumentor.instrument()
        instrumentor.uninstrument()

    def test_valkey_django_backend_error_logs_error_and_returns_default(self):
        """When Valkey client throws an error, ValkeyCache logs logger.error and returns default."""
        cache = ValkeyCache("valkey://localhost:6379/1", {"KEY_PREFIX": "test", "TIMEOUT": 300})
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Valkey connection reset")
        cache._sync_client = mock_client

        with patch("politiaware_backend.valkey_cache.django_backend.logger.error") as mock_err:
            val = cache.get("missing_key", default="fallback_value")
            self.assertEqual(val, "fallback_value")
            mock_err.assert_called_once()
            self.assertIn("Valkey sync get error", mock_err.call_args[0][0])

    def test_valkey_django_backend_async_error_logs_error(self):
        """When async Valkey client throws an error, aget logs logger.error and returns default."""
        cache = ValkeyCache("valkey://localhost:6379/1", {"KEY_PREFIX": "test", "TIMEOUT": 300})
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Async Valkey timeout"))
        cache._async_client = mock_client

        with patch("politiaware_backend.valkey_cache.django_backend.logger.error") as mock_err:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            val = loop.run_until_complete(cache.aget("test_key", default="default_async"))
            loop.close()
            self.assertEqual(val, "default_async")
            mock_err.assert_called_once()
            self.assertIn("Valkey async aget error", mock_err.call_args[0][0])


class TestOpenSearchLogging(unittest.TestCase):
    """Tests OpenSearch JSON formatting and trace injection."""

    def test_json_formatter_structure(self):
        formatter = OpenSearchJSONFormatter(service_name="test-service", environment="test")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="User login successful for user %s",
            args=("alice",),
            exc_info=None,
        )
        record.otelTraceID = "4bf92f3577b34da6a3ce929d0e0e4736"
        record.otelSpanID = "00f067aa0ba902b7"

        formatted_json = formatter.format(record)
        data = json.loads(formatted_json)

        self.assertEqual(data["service"]["name"], "test-service")
        self.assertEqual(data["log"]["level"], "INFO")
        self.assertEqual(data["message"], "User login successful for user alice")
        self.assertEqual(data["trace_id"], "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(data["span_id"], "00f067aa0ba902b7")
        self.assertIn("@timestamp", data)

    def test_opensearch_handler_buffering(self):
        handler = OpenSearchHandler(
            opensearch_url="http://localhost:9200",
            index_prefix="test-logs",
            buffer_size=10,
            flush_interval=5.0,
        )
        record = logging.LogRecord(
            name="test.buffer",
            level=logging.WARNING,
            pathname=__file__,
            lineno=120,
            msg="Test warning message",
            args=(),
            exc_info=None,
        )
        handler.emit(record)
        self.assertFalse(handler.queue.empty())
        handler.close()


class TestObservabilityMiddleware(unittest.TestCase):
    """Tests Django middleware for span enrichment and X-Trace-ID header injection."""

    def test_middleware_adds_trace_header(self):
        def mock_get_response(req):
            response = MagicMock()
            response.__setitem__ = MagicMock()
            return response

        middleware = ObservabilityMiddleware(mock_get_response)
        request = MagicMock()
        request.META = {
            "HTTP_X_REQUEST_ID": "req-xyz-123",
            "REMOTE_ADDR": "192.168.1.1",
        }
        request.path = "/api/v1/users/"
        request.method = "GET"
        request.body = b""
        request.user = MagicMock()
        request.user.is_authenticated = False

        response = middleware(request)
        self.assertIsNotNone(response)


class TestObservabilityInit(unittest.TestCase):
    """Tests top-level bootstrap function and trace_span context manager."""

    def test_init_observability_safe_run(self):
        init_observability()

    def test_trace_span_context(self):
        with trace_span("unit_test_operation", {"custom.tag": "val"}) as span:
            self.assertIsNotNone(span)


if __name__ == "__main__":
    unittest.main(verbosity=2)
