"""
Root-level proxy for politiaware_backend.observability.
Allows importing as either `from observability import ...` or `from politiaware_backend.observability import ...`
"""

from politiaware_backend.observability import (
    init_observability,
    get_tracer,
    trace_span,
    config,
    wrap_asgi_application,
    wrap_wsgi_application,
    get_strawberry_otel_extension,
    ValkeyInstrumentor,
    OpenSearchHandler,
    OpenSearchJSONFormatter,
    ObservabilityMiddleware,
)

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

