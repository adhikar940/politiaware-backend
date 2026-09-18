"""
Outbound HTTP Clients OpenTelemetry Auto-Instrumentation.
Instruments requests, httpx, urllib3, and standard urllib.
Ensures trace context (W3C traceparent headers) propagates across external API calls.
"""

import logging
from ..config import config

logger = logging.getLogger("observability.instrumentors.http")

_INSTRUMENTED = False


def instrument_http_clients():
    """Instruments outbound HTTP clients."""
    global _INSTRUMENTED
    if _INSTRUMENTED or not config.instrument_http:
        return

    # 1. requests
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
        logger.info("requests auto-instrumentation enabled.")
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error instrumenting requests: %s", exc)

    # 2. httpx
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
        logger.info("httpx auto-instrumentation enabled.")
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error instrumenting httpx: %s", exc)

    # 3. urllib3
    try:
        from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
        URLLib3Instrumentor().instrument()
        logger.info("urllib3 auto-instrumentation enabled.")
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error instrumenting urllib3: %s", exc)

    # 4. urllib
    try:
        from opentelemetry.instrumentation.urllib import URLLibInstrumentor
        URLLibInstrumentor().instrument()
        logger.info("urllib auto-instrumentation enabled.")
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error instrumenting urllib: %s", exc)

    _INSTRUMENTED = True


def uninstrument_http_clients():
    """Uninstruments HTTP clients."""
    global _INSTRUMENTED
    if not _INSTRUMENTED:
        return

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().uninstrument()
    except Exception:
        pass

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().uninstrument()
    except Exception:
        pass

    try:
        from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
        URLLib3Instrumentor().uninstrument()
    except Exception:
        pass

    try:
        from opentelemetry.instrumentation.urllib import URLLibInstrumentor
        URLLibInstrumentor().uninstrument()
    except Exception:
        pass

    _INSTRUMENTED = False

