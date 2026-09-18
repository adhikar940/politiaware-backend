"""
Asynchronous Strawberry GraphQL Schema for Politiaware Backend.
Dynamically generated from generic_async_graphql and GRAPHQL_CONF.
"""

from generic_async_graphql import generate_generic_async_graphql
from graphql_conf.graphql_conf import GRAPHQL_CONF

# Strawberry extensions for OpenTelemetry tracing
extensions = []
try:
    from politiaware_backend.observability import get_strawberry_otel_extension
    otel_ext = get_strawberry_otel_extension()
    if otel_ext:
        extensions.append(otel_ext())
except Exception:
    pass

# Build the compiled Strawberry async schema
async_schema = generate_generic_async_graphql(GRAPHQL_CONF, extensions=extensions)


