"""
Asynchronous Valkey / Redis Caching Service.

Features:
1. Configurable via environment variables (ENABLE_VALKEY_CACHE, VALKEY_URL, VALKEY_CACHE_TTL, VALKEY_PREFIX).
2. Fully non-blocking via valkey.asyncio (official Linux Foundation Valkey client).
3. RedisInsight-friendly key hierarchy:
   - Payload:  <prefix>:graphql:<model>:list:<query_hash>
   - Metadata: <prefix>:graphql:<model>:list:<query_hash>:meta  (human-readable JSON)
   - Tracking: <prefix>:keys:<model>                            (Redis Set of active keys)
4. Fast invalidation on mutations:
   - When a model is created/updated/deleted, all active cache keys for that model are purged.
5. Resilient fallback:
   - If cache is disabled or Valkey is unreachable, gracefully returns None (bypasses to DB)
     with zero disruption or crashes.
"""

import os
import json
import pickle
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple, Type
from datetime import datetime, timezone

try:
    from django.conf import settings
except ImportError:
    settings = None

try:
    from django.db import models
except ImportError:
    models = None

logger = logging.getLogger(__name__)

# Import official Valkey async client (valkey-py)
try:
    import valkey.asyncio as aiovalkey
    HAS_VALKEY = True
except ImportError:
    try:
        import redis.asyncio as aiovalkey
        HAS_VALKEY = True
    except ImportError:
        aiovalkey = None
        HAS_VALKEY = False


# ---------------------------------------------------------------------------
# CONFIGURATION HELPERS
# ---------------------------------------------------------------------------

def _to_bool(val: Any, default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in ("true", "1", "yes", "on")


def is_cache_enabled() -> bool:
    """Checks whether Valkey caching is currently enabled."""
    if not HAS_VALKEY:
        return False

    # Check Django settings first, then env var fallback
    if settings is not None:
        try:
            enabled_setting = getattr(settings, "ENABLE_VALKEY_CACHE", None)
            if enabled_setting is not None:
                return bool(enabled_setting)
        except Exception:
            pass
    return _to_bool(os.getenv("ENABLE_VALKEY_CACHE", "False"), default=False)


def get_valkey_url() -> str:
    """Returns the connection URL for Valkey."""
    if settings is not None:
        try:
            url = getattr(settings, "VALKEY_URL", None)
            if url:
                return url
        except Exception:
            pass
    return os.getenv("VALKEY_URL", "valkey://127.0.0.1:6379/1")


def get_default_ttl() -> int:
    """Returns the default TTL in seconds (default: 3600 = 1 hour)."""
    val = None
    if settings is not None:
        try:
            val = getattr(settings, "VALKEY_CACHE_TTL", None)
        except Exception:
            pass
    if val is None:
        val = os.getenv("VALKEY_CACHE_TTL", "3600")
    try:
        return int(val)
    except (ValueError, TypeError):
        return 3600


def get_key_prefix() -> str:
    """Returns the global key prefix for namespace separation (default: politiaware)."""
    if settings is not None:
        try:
            prefix = getattr(settings, "VALKEY_PREFIX", None)
            if prefix:
                return prefix
        except Exception:
            pass
    return os.getenv("VALKEY_PREFIX", "politiaware")


# ---------------------------------------------------------------------------
# CLIENT SINGLETON
# ---------------------------------------------------------------------------

_VALKEY_CLIENT: Optional[Any] = None


def get_valkey_client():
    """Returns a shared asynchronous Valkey client instance."""
    global _VALKEY_CLIENT
    if _VALKEY_CLIENT is None and HAS_VALKEY:
        url = get_valkey_url()
        _VALKEY_CLIENT = aiovalkey.from_url(
            url,
            encoding="utf-8",
            decode_responses=False,  # Keep binary support for pickled model payloads
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
    return _VALKEY_CLIENT


# ---------------------------------------------------------------------------
# KEY GENERATION & REDISINSIGHT STRUCTURING
# ---------------------------------------------------------------------------

def _make_hashable(val: Any) -> Any:
    """Recursively converts dicts, lists, and types to deterministic hashable formats."""
    if isinstance(val, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in val.items() if v is not None))
    elif isinstance(val, (list, tuple, set)):
        return tuple(_make_hashable(v) for v in val)
    elif val is None:
        return None
    return str(val)


def build_list_cache_key(
    model_cls: Type[models.Model],
    filters_data: Optional[Dict[str, Any]] = None,
    search_term: Optional[str] = None,
    search_fields: Optional[List[str]] = None,
    order_by: Optional[Any] = None,
    offset: int = 0,
    limit: int = 10,
    select_paths: Optional[List[str]] = None,
) -> Tuple[str, str, str, Dict[str, Any]]:
    """
    Builds deterministic cache keys:
    Returns:
      (payload_key, meta_key, tracking_set_key, metadata_dict)
    """
    prefix = get_key_prefix()
    app_label = model_cls._meta.app_label.lower()
    model_name = model_cls.__name__.lower()

    # Create deterministic representation of all query parameters
    query_params = {
        "filters": _make_hashable(filters_data) if filters_data else None,
        "search": search_term,
        "search_fields": sorted(search_fields) if search_fields else None,
        "order_by": order_by,
        "offset": offset,
        "limit": limit,
        "select_paths": sorted(select_paths) if select_paths else None,
    }

    params_bytes = repr(query_params).encode("utf-8")
    query_hash = hashlib.sha256(params_bytes).hexdigest()[:16]

    # Structure keys using colons so RedisInsight groups them into folders
    payload_key = f"{prefix}:graphql:{model_name}:list:{query_hash}"
    meta_key = f"{prefix}:graphql:{model_name}:list:{query_hash}:meta"
    tracking_set_key = f"{prefix}:keys:{model_name}"

    metadata = {
        "model": model_cls.__name__,
        "app_label": app_label,
        "offset": offset,
        "limit": limit,
        "search": search_term,
        "order_by": order_by,
        "has_filters": bool(filters_data),
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }

    return payload_key, meta_key, tracking_set_key, metadata


# ---------------------------------------------------------------------------
# ASYNC CACHE OPERATIONS
# ---------------------------------------------------------------------------

async def aget_cached_list(payload_key: str) -> Optional[Dict[str, Any]]:
    """
    Asynchronously retrieves a cached list query result from Valkey.
    Returns None if cache is disabled, key not found, or on connection error.
    """
    if not is_cache_enabled():
        return None

    client = get_valkey_client()
    if not client:
        return None

    try:
        raw_bytes = await client.get(payload_key)
        if raw_bytes is not None:
            return pickle.loads(raw_bytes)
    except Exception as e:
        logger.error("Valkey cache read error for key '%s': %s", payload_key, e)
        return None

    return None


async def aset_cached_list(
    payload_key: str,
    meta_key: str,
    tracking_set_key: str,
    result_dict: Dict[str, Any],
    metadata: Dict[str, Any],
    ttl: Optional[int] = None
) -> None:
    """
    Asynchronously saves query result and human-readable metadata to Valkey.
    Also registers the key in the model's tracking set for fast invalidation.
    """
    if not is_cache_enabled():
        return

    client = get_valkey_client()
    if not client:
        return

    timeout = ttl if ttl is not None else get_default_ttl()

    try:
        # 1. Store pickled payload for maximum Python/Django fidelity
        payload_bytes = pickle.dumps(result_dict)
        await client.set(payload_key, payload_bytes, ex=timeout)

        # 2. Store readable JSON metadata for inspection in RedisInsight
        metadata["total"] = result_dict.get("total", 0)
        metadata["ttl_seconds"] = timeout
        meta_json = json.dumps(metadata, indent=2).encode("utf-8")
        await client.set(meta_key, meta_json, ex=timeout)

        # 3. Track keys in model Set for easy invalidation on mutations
        await client.sadd(tracking_set_key, payload_key.encode("utf-8"), meta_key.encode("utf-8"))
        await client.expire(tracking_set_key, timeout + 300)
    except Exception as e:
        logger.error("Valkey cache write error for key '%s': %s", payload_key, e)


async def ainvalidate_model(model_cls: Type[models.Model]) -> int:
    """
    Asynchronously purges all cached queries for a given model.
    Called automatically when create, update, or delete mutations run.
    Returns the number of keys purged.
    """
    if not is_cache_enabled():
        return 0

    client = get_valkey_client()
    if not client:
        return 0

    prefix = get_key_prefix()
    model_name = model_cls.__name__.lower()
    tracking_set_key = f"{prefix}:keys:{model_name}"

    try:
        keys_to_delete = await client.smembers(tracking_set_key)
        deleted_count = 0
        if keys_to_delete:
            deleted_count = await client.delete(*keys_to_delete)
        # Delete the tracking set itself
        await client.delete(tracking_set_key)
        logger.info("Purged %d Valkey cache keys for model '%s'", deleted_count, model_cls.__name__)
        return deleted_count
    except Exception as e:
        logger.error("Valkey cache invalidation error for model '%s': %s", model_cls.__name__, e)
        return 0

