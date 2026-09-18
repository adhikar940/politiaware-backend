"""
Valkey and Redis OpenTelemetry Auto-Instrumentation.
Provides dedicated OpenTelemetry tracing for both:
1. Official Valkey client (valkey-py, valkey.asyncio, valkey.Redis)
2. Redis client (redis-py, redis.asyncio, redis.Redis)
"""

import functools
import inspect
import logging
from typing import Any, Callable, Optional

from ..config import config

logger = logging.getLogger("observability.instrumentors.valkey")

_INSTRUMENTED = False
_ORIG_VALKEY_SYNC_EXECUTE = None
_ORIG_VALKEY_ASYNC_EXECUTE = None
_ORIG_VALKEY_SYNC_PIPELINE = None
_ORIG_VALKEY_ASYNC_PIPELINE = None


def _format_statement(command: str, args: tuple) -> str:
    """Formats safe db.statement string without exposing large binary payloads."""
    cmd_str = str(command).upper()
    if not args:
        return cmd_str
    # Truncate or redact large values (e.g. SET key <large-payload>)
    first_arg = str(args[0]) if len(args) > 0 else ""
    if cmd_str in ("SET", "SETEX", "PSETEX", "ASET"):
        return f"{cmd_str} {first_arg} <payload>"
    elif len(args) > 3:
        return f"{cmd_str} {first_arg} ... ({len(args)} args)"
    return f"{cmd_str} {' '.join(str(a) for a in args)}"


def _wrap_valkey_sync_execute(orig_func: Callable):
    @functools.wraps(orig_func)
    def wrapper(self, *args, **kwargs):
        from opentelemetry import trace
        from opentelemetry.trace import SpanKind, StatusCode

        tracer = trace.get_tracer("observability.valkey")
        cmd = args[0] if args else "COMMAND"
        span_name = f"valkey.{str(cmd).upper()}"

        with tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT) as span:
            if span.is_recording():
                span.set_attribute("db.system", "valkey")
                span.set_attribute("db.operation", str(cmd).upper())
                span.set_attribute("db.statement", _format_statement(str(cmd), args[1:]))
                conn_kwargs = getattr(self, "connection_pool", None)
                if conn_kwargs and hasattr(conn_kwargs, "connection_kwargs"):
                    ck = conn_kwargs.connection_kwargs
                    span.set_attribute("net.peer.name", ck.get("host", "localhost"))
                    span.set_attribute("net.peer.port", int(ck.get("port", 6379)))

            try:
                result = orig_func(self, *args, **kwargs)
                return result
            except Exception as exc:
                logger.error("Valkey command '%s' execution failed: %s", cmd, exc)
                span.record_exception(exc)
                span.set_status(StatusCode.ERROR, str(exc))
                raise

    return wrapper


def _wrap_valkey_async_execute(orig_func: Callable):
    @functools.wraps(orig_func)
    async def wrapper(self, *args, **kwargs):
        from opentelemetry import trace
        from opentelemetry.trace import SpanKind, StatusCode

        tracer = trace.get_tracer("observability.valkey")
        cmd = args[0] if args else "COMMAND"
        span_name = f"valkey.{str(cmd).upper()}"

        with tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT) as span:
            if span.is_recording():
                span.set_attribute("db.system", "valkey")
                span.set_attribute("db.operation", str(cmd).upper())
                span.set_attribute("db.statement", _format_statement(str(cmd), args[1:]))
                conn_kwargs = getattr(self, "connection_pool", None)
                if conn_kwargs and hasattr(conn_kwargs, "connection_kwargs"):
                    ck = conn_kwargs.connection_kwargs
                    span.set_attribute("net.peer.name", ck.get("host", "localhost"))
                    span.set_attribute("net.peer.port", int(ck.get("port", 6379)))

            try:
                result = await orig_func(self, *args, **kwargs)
                return result
            except Exception as exc:
                logger.error("Valkey async command '%s' execution failed: %s", cmd, exc)
                span.record_exception(exc)
                span.set_status(StatusCode.ERROR, str(exc))
                raise

    return wrapper


class ValkeyInstrumentor:
    """Dedicated instrumentor for the official Valkey client (valkey-py)."""

    def instrument(self):
        global _ORIG_VALKEY_SYNC_EXECUTE, _ORIG_VALKEY_ASYNC_EXECUTE

        # 1. Sync Valkey
        try:
            import valkey
            if hasattr(valkey, "Redis") and _ORIG_VALKEY_SYNC_EXECUTE is None:
                _ORIG_VALKEY_SYNC_EXECUTE = valkey.Redis.execute_command
                valkey.Redis.execute_command = _wrap_valkey_sync_execute(_ORIG_VALKEY_SYNC_EXECUTE)
                logger.info("valkey (sync) auto-instrumentation applied.")
        except ImportError:
            pass
        except Exception as exc:
            logger.warning("Failed to instrument sync valkey: %s", exc)

        # 2. Async Valkey
        try:
            import valkey.asyncio as aiovalkey
            if hasattr(aiovalkey, "Redis") and _ORIG_VALKEY_ASYNC_EXECUTE is None:
                _ORIG_VALKEY_ASYNC_EXECUTE = aiovalkey.Redis.execute_command
                aiovalkey.Redis.execute_command = _wrap_valkey_async_execute(_ORIG_VALKEY_ASYNC_EXECUTE)
                logger.info("valkey.asyncio auto-instrumentation applied.")
        except ImportError:
            pass
        except Exception as exc:
            logger.warning("Failed to instrument async valkey: %s", exc)

    def uninstrument(self):
        global _ORIG_VALKEY_SYNC_EXECUTE, _ORIG_VALKEY_ASYNC_EXECUTE
        try:
            import valkey
            if _ORIG_VALKEY_SYNC_EXECUTE is not None and hasattr(valkey, "Redis"):
                valkey.Redis.execute_command = _ORIG_VALKEY_SYNC_EXECUTE
                _ORIG_VALKEY_SYNC_EXECUTE = None
        except Exception:
            pass

        try:
            import valkey.asyncio as aiovalkey
            if _ORIG_VALKEY_ASYNC_EXECUTE is not None and hasattr(aiovalkey, "Redis"):
                aiovalkey.Redis.execute_command = _ORIG_VALKEY_ASYNC_EXECUTE
                _ORIG_VALKEY_ASYNC_EXECUTE = None
        except Exception:
            pass


def instrument_valkey():
    """Instruments both Redis and Valkey."""
    global _INSTRUMENTED
    if _INSTRUMENTED or not config.instrument_valkey:
        return

    # Instrument valkey-py
    ValkeyInstrumentor().instrument()

    # Instrument redis-py if present
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
        logger.info("redis-py auto-instrumentation enabled.")
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error instrumenting redis: %s", exc)

    _INSTRUMENTED = True


def uninstrument_valkey():
    """Uninstruments Valkey and Redis."""
    global _INSTRUMENTED
    if not _INSTRUMENTED:
        return

    ValkeyInstrumentor().uninstrument()
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().uninstrument()
    except Exception:
        pass
    _INSTRUMENTED = False

