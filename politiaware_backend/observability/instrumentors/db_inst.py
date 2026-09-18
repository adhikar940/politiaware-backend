"""
Database (PostgreSQL / PostGIS) OpenTelemetry Auto-Instrumentation.
Instruments psycopg2, psycopg (v3), and DBAPI drivers.
"""

import logging
from ..config import config

logger = logging.getLogger("observability.instrumentors.db")

_INSTRUMENTED = False


def instrument_database():
    """Applies OpenTelemetry instrumentation to database drivers."""
    global _INSTRUMENTED
    if _INSTRUMENTED or not config.instrument_db:
        return

    instrumented_any = False

    # 1. psycopg2
    try:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
        Psycopg2Instrumentor().instrument(enable_commenter=True)
        instrumented_any = True
        logger.info("psycopg2 auto-instrumentation enabled.")
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error instrumenting psycopg2: %s", exc)

    # 2. psycopg (v3)
    try:
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        PsycopgInstrumentor().instrument(enable_commenter=True)
        instrumented_any = True
        logger.info("psycopg (v3) auto-instrumentation enabled.")
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error instrumenting psycopg (v3): %s", exc)

    # 3. dbapi generic trace integration
    try:
        from opentelemetry.instrumentation.dbapi import trace_integration
        trace_integration(enable=True)
    except (ImportError, Exception):
        pass

    if instrumented_any:
        _INSTRUMENTED = True


def uninstrument_database():
    """Uninstruments database drivers."""
    global _INSTRUMENTED
    if not _INSTRUMENTED:
        return
    try:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
        Psycopg2Instrumentor().uninstrument()
    except Exception:
        pass
    try:
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        PsycopgInstrumentor().uninstrument()
    except Exception:
        pass
    _INSTRUMENTED = False

