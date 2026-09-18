"""
ASGI (Uvicorn) and WSGI (Gunicorn) OpenTelemetry Instrumentation.
"""

import logging
from ..config import config

logger = logging.getLogger("observability.instrumentors.server")


def wrap_asgi_application(application):
    """
    Wraps an ASGI application (such as Django's get_asgi_application())
    with OpenTelemetry ASGI middleware.
    """
    if not config.enabled or not config.instrument_servers:
        return application

    try:
        from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
        logger.info("Wrapped ASGI application with OpenTelemetryMiddleware.")
        return OpenTelemetryMiddleware(application)
    except ImportError:
        logger.debug("opentelemetry-instrumentation-asgi not installed.")
        return application
    except Exception as exc:
        logger.warning("Failed to wrap ASGI application: %s", exc)
        return application


def wrap_wsgi_application(application):
    """
    Wraps a WSGI application (such as Django's get_wsgi_application())
    with OpenTelemetry WSGI middleware.
    """
    if not config.enabled or not config.instrument_servers:
        return application

    try:
        from opentelemetry.instrumentation.wsgi import OpenTelemetryMiddleware
        logger.info("Wrapped WSGI application with OpenTelemetryMiddleware.")
        return OpenTelemetryMiddleware(application)
    except ImportError:
        logger.debug("opentelemetry-instrumentation-wsgi not installed.")
        return application
    except Exception as exc:
        logger.warning("Failed to wrap WSGI application: %s", exc)
        return application

