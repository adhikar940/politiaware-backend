"""
Valkey Cache Module for Politiaware Backend.

Exports:
- Cache Service Layer (Async GraphQL):
    is_cache_enabled,
    get_valkey_url,
    get_default_ttl,
    get_key_prefix,
    build_list_cache_key,
    aget_cached_list,
    aset_cached_list,
    ainvalidate_model

- Django Cache Backend (Official valkey-py):
    ValkeyCache
"""

from .cache_service import (
    is_cache_enabled,
    get_valkey_url,
    get_default_ttl,
    get_key_prefix,
    build_list_cache_key,
    aget_cached_list,
    aset_cached_list,
    ainvalidate_model,
)
from .django_backend import ValkeyCache

__all__ = [
    "is_cache_enabled",
    "get_valkey_url",
    "get_default_ttl",
    "get_key_prefix",
    "build_list_cache_key",
    "aget_cached_list",
    "aset_cached_list",
    "ainvalidate_model",
    "ValkeyCache",
]

