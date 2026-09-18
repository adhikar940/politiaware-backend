"""
Django OpenTelemetry Auto-Instrumentation.
Instruments Django views, middleware, URL routing, and request/response lifecycles.
"""

import logging
from ..config import config

logger = logging.getLogger("observability.instrumentors.django")

_INSTRUMENTED = False


def instrument_django():
    """Applies OpenTelemetry instrumentation to Django."""
    global _INSTRUMENTED
    if _INSTRUMENTED or not config.instrument_django:
        return

    try:
        from opentelemetry.instrumentation.django import DjangoInstrumentor
    except ImportError:
        logger.debug("opentelemetry-instrumentation-django not installed. Skipping Django instrumentation.")
        return

    try:
        # Pass excluded URLs (comma-separated, regex or wildcard supported)
        excluded_urls = config.excluded_urls
        DjangoInstrumentor().instrument(
            excluded_urls=excluded_urls,
            is_sql_commentor_enabled=True,
        )
        _INSTRUMENTED = True
        logger.info("Django auto-instrumentation enabled (excluded_urls='%s').", excluded_urls)
    except Exception as exc:
        logger.warning("Failed to instrument Django with OpenTelemetry: %s", exc)


def uninstrument_django():
    """Uninstruments Django."""
    global _INSTRUMENTED
    if not _INSTRUMENTED:
        return
    try:
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        DjangoInstrumentor().uninstrument()
        _INSTRUMENTED = False
    except Exception as exc:
        logger.warning("Failed to uninstrument Django: %s", exc)

