"""
Observability Logging Package.
Provides OpenTelemetry log correlation and asynchronous streaming to OpenSearch.
"""

import logging
from ..config import config
from .formatters import OpenSearchJSONFormatter
from .opensearch_handler import OpenSearchHandler

logger = logging.getLogger("observability.logging")

_LOGGING_INSTRUMENTED = False
_OPENSEARCH_HANDLER_ATTACHED = False


def instrument_logging():
    """
    Enables OpenTelemetry logging instrumentation.
    Injects otelTraceID, otelSpanID, and otelServiceName into standard LogRecord instances.
    """
    global _LOGGING_INSTRUMENTED
    if _LOGGING_INSTRUMENTED or not config.instrument_logging:
        return

    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        LoggingInstrumentor().instrument(set_logging_format=False)
        _LOGGING_INSTRUMENTED = True
        logger.info("OpenTelemetry logging correlation instrumentor activated.")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-logging not installed.")
    except Exception as exc:
        logger.warning("Failed to instrument logging with OpenTelemetry: %s", exc)


def setup_opensearch_logging(level: int = logging.INFO):
    """
    Attaches the asynchronous OpenSearchHandler to the root Python logger.
    """
    global _OPENSEARCH_HANDLER_ATTACHED
    if _OPENSEARCH_HANDLER_ATTACHED or not config.opensearch_logging_enabled:
        return

    root_logger = logging.getLogger()
    # Check if an OpenSearchHandler is already attached
    for handler in root_logger.handlers:
        if isinstance(handler, OpenSearchHandler):
            _OPENSEARCH_HANDLER_ATTACHED = True
            return

    os_handler = OpenSearchHandler(
        opensearch_url=config.opensearch_url,
        index_prefix=config.opensearch_index_prefix,
        level=level,
    )
    root_logger.addHandler(os_handler)
    _OPENSEARCH_HANDLER_ATTACHED = True
    logger.info("Attached OpenSearchHandler to root logger (target: %s).", config.opensearch_url)


__all__ = [
    "OpenSearchHandler",
    "OpenSearchJSONFormatter",
    "instrument_logging",
    "setup_opensearch_logging",
]
