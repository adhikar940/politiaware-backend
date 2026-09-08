"""
Asynchronous Strawberry GraphQL Schema for Politiaware Backend.
Dynamically generated from generic_async_graphql and TOML / GRAPHQL_CONF.
"""

from politiaware_backend.generic_async_graphql import generate_generic_async_graphql

try:
    from politiaware_backend.graphql_conf.graphql_conf import GRAPHQL_CONF
except ImportError:
    GRAPHQL_CONF = None

# Build the compiled Strawberry async schema (loads models from .toml if GRAPHQL_CONF is None)
async_schema = generate_generic_async_graphql(GRAPHQL_CONF)
