"""
GraphQL (Strawberry GraphQL and graphql-core) OpenTelemetry Auto-Instrumentation.
"""

import logging
from typing import List, Optional

from ..config import config

logger = logging.getLogger("observability.instrumentors.graphql")

_INSTRUMENTED = False


def instrument_graphql():
    """Instruments underlying graphql-core execution."""
    global _INSTRUMENTED
    if _INSTRUMENTED or not config.instrument_graphql:
        return

    try:
        from opentelemetry.instrumentation.graphql import GraphQLInstrumentor
        GraphQLInstrumentor().instrument()
        _INSTRUMENTED = True
        logger.info("graphql-core auto-instrumentation enabled.")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-graphql not installed. Skipping graphql-core instrumentation.")
    except Exception as exc:
        logger.warning("Failed to instrument graphql-core: %s", exc)


def uninstrument_graphql():
    """Uninstruments graphql-core."""
    global _INSTRUMENTED
    if not _INSTRUMENTED:
        return
    try:
        from opentelemetry.instrumentation.graphql import GraphQLInstrumentor
        GraphQLInstrumentor().uninstrument()
        _INSTRUMENTED = False
    except Exception as exc:
        logger.warning("Failed to uninstrument graphql-core: %s", exc)


def get_strawberry_otel_extension():
    """
    Returns the Strawberry OpenTelemetryExtension instance to be passed into
    the Strawberry Schema(extensions=[...]).
    """
    if not config.enabled or not config.instrument_graphql:
        return None

    try:
        from strawberry.extensions.tracing import OpenTelemetryExtension
        logger.debug("Strawberry OpenTelemetryExtension loaded.")
        return OpenTelemetryExtension
    except ImportError:
        pass

    # Fallback to custom Strawberry extension if built-in is unavailable
    try:
        from strawberry.extensions import SchemaExtension
        from opentelemetry import trace
        from opentelemetry.trace import SpanKind

        class CustomStrawberryOtelExtension(SchemaExtension):
            def on_operation(self):
                tracer = trace.get_tracer("strawberry.graphql")
                op_name = self.execution_context.operation_name or "GraphQL_Operation"
                span = tracer.start_span(
                    f"graphql.{op_name}",
                    kind=SpanKind.SERVER,
                )
                span.set_attribute("graphql.operation.name", str(op_name))
                yield
                span.end()

        return CustomStrawberryOtelExtension
    except Exception:
        return None

