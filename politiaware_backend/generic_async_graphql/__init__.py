"""
Generic Asynchronous GraphQL Engine (generic_async_graphql).
Powered by Strawberry GraphQL and an isolated, thread-safe db_operations service layer.
"""

from .builder import generate_generic_async_graphql, generate_generic_async_types
from .async_db_operations import (
    async_fetch_list,
    async_create_record,
    async_update_record,
    async_partial_update_record,
    async_delete_record,
    parse_nested_filters
)
from .sync_db_operations import (
    sync_create_record,
    sync_update_record,
    sync_partial_update_record,
    sync_delete_record
)
from .type_factory import DeletePayload

__all__ = [
    "generate_generic_async_graphql",
    "generate_generic_async_types",
    "async_fetch_list",
    "async_create_record",
    "async_update_record",
    "async_partial_update_record",
    "async_delete_record",
    "parse_nested_filters",
    "sync_create_record",
    "sync_update_record",
    "sync_partial_update_record",
    "sync_delete_record",
    "DeletePayload",
]

