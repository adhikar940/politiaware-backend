"""
Auto-Instrumentation Orchestrator.
Safely detects available libraries and activates corresponding OpenTelemetry instrumentors.
"""

import logging
from ..config import config
from .django_inst import instrument_django, uninstrument_django
from .db_inst import instrument_database, uninstrument_database
from .valkey_inst import instrument_valkey, uninstrument_valkey, ValkeyInstrumentor
from .graphql_inst import instrument_graphql, uninstrument_graphql, get_strawberry_otel_extension
from .server_inst import wrap_asgi_application, wrap_wsgi_application
from .http_inst import instrument_http_clients, uninstrument_http_clients

logger = logging.getLogger("observability.instrumentors")


def instrument_all():
    """
    Safely auto-instruments all components in the politiaware stack:
    - Django HTTP requests, views, URLs, and middleware
    - PostgreSQL / PostGIS database drivers (psycopg2, psycopg)
    - Valkey (official valkey-py) and Redis cache operations
    - Strawberry GraphQL and graphql-core
    - Outbound HTTP clients (requests, httpx, urllib3)
    """
    if not config.enabled:
        return

    logger.info("Auto-instrumenting Politiaware application components...")

    # 1. Django Framework
    instrument_django()

    # 2. Database (PostgreSQL / PostGIS)
    instrument_database()

    # 3. Cache (Valkey / Redis)
    instrument_valkey()

    # 4. GraphQL (Strawberry & graphql-core)
    instrument_graphql()

    # 5. Outbound HTTP
    instrument_http_clients()

    logger.info("All applicable auto-instrumentors activated.")


def uninstrument_all():
    """Removes all active OpenTelemetry instrumentations."""
    uninstrument_django()
    uninstrument_database()
    uninstrument_valkey()
    uninstrument_graphql()
    uninstrument_http_clients()


__all__ = [
    "instrument_all",
    "uninstrument_all",
    "instrument_django",
    "instrument_database",
    "instrument_valkey",
    "instrument_graphql",
    "instrument_http_clients",
    "wrap_asgi_application",
    "wrap_wsgi_application",
    "get_strawberry_otel_extension",
    "ValkeyInstrumentor",
]

