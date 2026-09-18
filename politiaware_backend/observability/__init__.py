"""
Politiaware Backend Observability Suite.
Centralized OpenTelemetry Tracing, Metrics, and OpenSearch Logging for:
- Django Framework & Middlewares
- PostgreSQL / PostGIS (psycopg2 & psycopg)
- Valkey (official valkey-py) and Redis Cache
- Strawberry GraphQL & graphql-core
- Outbound HTTP Clients (requests, httpx, urllib3)
- ASGI (Uvicorn) & WSGI (Gunicorn) Servers
- Distributed Trace Correlated Logging -> OpenSearch
- Jaeger OTLP Exporter
"""

import logging
from contextlib import contextmanager
from typing import Optional

from .config import config
from .tracer import init_tracer, get_tracer
from .instrumentors import (
    instrument_all,
    uninstrument_all,
    wrap_asgi_application,
    wrap_wsgi_application,
    get_strawberry_otel_extension,
    ValkeyInstrumentor,
)
from .logs import (
    instrument_logging,
    setup_opensearch_logging,
    OpenSearchHandler,
    OpenSearchJSONFormatter,
)
from .middleware import ObservabilityMiddleware

logger = logging.getLogger("observability")

_BOOTSTRAPPED = False


def init_observability():
    """
    Initializes the entire observability suite:
    1. Sets up OpenTelemetry TracerProvider with Jaeger OTLP exporter.
    2. Auto-instruments Django, PostgreSQL, Valkey, GraphQL, and HTTP clients.
    3. Instruments Python logging for trace correlation (otelTraceID, otelSpanID).
    4. Connects the asynchronous OpenSearch log handler.
    """
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    if not config.enabled:
        logger.info("Observability is disabled via configuration.")
        _BOOTSTRAPPED = True
        return

    logger.info("Initializing Politiaware Observability (Jaeger + OpenSearch)...")

    # 1. Initialize Tracer Provider & Jaeger Exporter
    init_tracer()

    # 2. Auto-instrument all supported application components
    instrument_all()

    # 3. Setup Logging correlation
    instrument_logging()

    # 4. Attach OpenSearch Log Handler if enabled
    if config.opensearch_logging_enabled:
        setup_opensearch_logging()

    _BOOTSTRAPPED = True
    logger.info("Politiaware Observability successfully initialized.")


@contextmanager
def trace_span(name: str, attributes: Optional[dict] = None):
    """
    Convenience context manager to trace a custom block of code.
    Usage:
        with trace_span("custom_task", {"item.id": 123}):
            perform_task()
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes and span and getattr(span, "is_recording", lambda: False)():
            for k, v in attributes.items():
                span.set_attribute(k, v)
        yield span


__all__ = [
    "init_observability",
    "get_tracer",
    "trace_span",
    "config",
    "wrap_asgi_application",
    "wrap_wsgi_application",
    "get_strawberry_otel_extension",
    "ValkeyInstrumentor",
    "OpenSearchHandler",
    "OpenSearchJSONFormatter",
    "ObservabilityMiddleware",
]
