"""
Test script for Valkey Caching Integration in politiaware_backend.valkey_cache.
Verifies:
1. Environment-variable toggle behavior (ENABLE_VALKEY_CACHE).
2. Deterministic cache key and RedisInsight metadata generation.
3. Non-blocking async cache operations (get, set, invalidation).
4. Graceful fallback when cache is disabled or connection unavailable.
"""

import os
import sys
import asyncio
import json
from unittest.mock import AsyncMock, patch

import importlib.util

# Load cache_service module directly to avoid triggering full strawberry/django init if not in venv
valkey_cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cache_service.py"))
spec = importlib.util.spec_from_file_location("cache_service", valkey_cache_path)
cache_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache_service)

is_cache_enabled = cache_service.is_cache_enabled
get_valkey_url = cache_service.get_valkey_url
get_default_ttl = cache_service.get_default_ttl
get_key_prefix = cache_service.get_key_prefix
build_list_cache_key = cache_service.build_list_cache_key
aget_cached_list = cache_service.aget_cached_list
aset_cached_list = cache_service.aset_cached_list
ainvalidate_model = cache_service.ainvalidate_model

class MockMeta:
    app_label = "party"

class Party:
    _meta = MockMeta
    __name__ = "Party"


def test_configuration_defaults():
    """Verify default configurations and environment handling."""
    print("\n--- Test 1: Configuration & Environment Defaults ---")
    # By default, cache should be disabled for safety
    assert not is_cache_enabled(), "Cache should be disabled by default (ENABLE_VALKEY_CACHE not set)"
    print("✅ Cache is disabled by default as intended.")

    ttl = get_default_ttl()
    assert ttl == 3600, f"Expected default TTL of 3600 (1 hour), got {ttl}"
    print(f"✅ Default TTL is {ttl}s (1 hour).")

    prefix = get_key_prefix()
    assert prefix == "politiaware", f"Expected prefix 'politiaware', got {prefix}"
    print(f"✅ Key prefix is '{prefix}'.")


def test_key_generation_and_redisinsight_structure():
    """Verify keys are structured cleanly with colons for RedisInsight folder view."""
    print("\n--- Test 2: RedisInsight Key & Metadata Structure ---")
    payload_key, meta_key, tracking_set_key, metadata = build_list_cache_key(
        model_cls=Party,
        filters_data={"partystatus": {"exact": "National"}},
        search_term="BJP",
        search_fields=["partyname"],
        order_by=["partyname"],
        offset=0,
        limit=10,
        select_paths=["state"]
    )

    print(f"  Generated Payload Key:      {payload_key}")
    print(f"  Generated Meta Key:         {meta_key}")
    print(f"  Generated Tracking Set Key: {tracking_set_key}")

    assert payload_key.startswith("politiaware:graphql:party:list:"), f"Invalid payload key: {payload_key}"
    assert meta_key.endswith(":meta"), f"Invalid meta key: {meta_key}"
    assert tracking_set_key == "politiaware:keys:party", f"Invalid tracking set key: {tracking_set_key}"
    assert metadata["model"] == "Party"
    assert metadata["search"] == "BJP"
    assert metadata["has_filters"] is True

    # Same arguments must produce identical cache keys (determinism)
    p2, m2, t2, _ = build_list_cache_key(
        model_cls=Party,
        filters_data={"partystatus": {"exact": "National"}},
        search_term="BJP",
        search_fields=["partyname"],
        order_by=["partyname"],
        offset=0,
        limit=10,
        select_paths=["state"]
    )
    assert payload_key == p2, "Cache keys must be deterministic"
    assert meta_key == m2, "Meta keys must be deterministic"
    print("✅ Cache keys and RedisInsight structures are deterministic and correctly formatted.")


async def test_disabled_cache_bypass():
    """Verify operations cleanly bypass cache when ENABLE_VALKEY_CACHE is False."""
    print("\n--- Test 3: Disabled Cache Bypass ---")
    with patch.object(cache_service, "is_cache_enabled", return_value=False):
        # aget should return None immediately
        res = await aget_cached_list("some_key")
        assert res is None
        print("✅ aget_cached_list returns None when cache is disabled.")

        # invalidation should return 0 immediately
        purged = await ainvalidate_model(Party)
        assert purged == 0
        print("✅ ainvalidate_model returns 0 when cache is disabled.")


async def test_async_caching_and_invalidation_flow():
    """Simulate cache storage, hit, and invalidation using mock Valkey client."""
    print("\n--- Test 4: Async Cache Save, Hit, and Invalidation Flow ---")

    fake_storage = {}
    fake_sets = {}

    mock_client = AsyncMock()

    async def fake_set(key, val, ex=None):
        fake_storage[key] = val

    async def fake_get(key):
        return fake_storage.get(key)

    async def fake_sadd(set_key, *keys):
        if set_key not in fake_sets:
            fake_sets[set_key] = set()
        for k in keys:
            fake_sets[set_key].add(k.decode() if isinstance(k, bytes) else k)

    async def fake_smembers(set_key):
        return fake_sets.get(set_key, set())

    async def fake_delete(*keys):
        count = 0
        for k in keys:
            key_str = k.decode() if isinstance(k, bytes) else k
            if key_str in fake_storage:
                del fake_storage[key_str]
                count += 1
            if key_str in fake_sets:
                del fake_sets[key_str]
        return count

    mock_client.set.side_effect = fake_set
    mock_client.get.side_effect = fake_get
    mock_client.sadd.side_effect = fake_sadd
    mock_client.smembers.side_effect = fake_smembers
    mock_client.delete.side_effect = fake_delete
    mock_client.expire = AsyncMock()

    with patch.object(cache_service, "is_cache_enabled", return_value=True), \
         patch.object(cache_service, "get_valkey_client", return_value=mock_client):


        payload_key, meta_key, tracking_set_key, metadata = build_list_cache_key(
            model_cls=Party,
            offset=0,
            limit=5
        )

        sample_result = {
            "total": 1,
            "offset": 0,
            "limit": 5,
            "data": [{"id": 1, "name": "Demo Party"}]
        }

        # 1. Save to cache
        await aset_cached_list(
            payload_key=payload_key,
            meta_key=meta_key,
            tracking_set_key=tracking_set_key,
            result_dict=sample_result,
            metadata=metadata,
            ttl=3600
        )
        assert payload_key in fake_storage, "Payload was not saved to fake Valkey"
        assert meta_key in fake_storage, "Metadata was not saved to fake Valkey"
        meta_content = json.loads(fake_storage[meta_key].decode())
        assert meta_content["model"] == "Party"
        assert meta_content["total"] == 1
        assert meta_content["ttl_seconds"] == 3600
        print("✅ Query payload and human-readable :meta JSON saved to Valkey.")

        # 2. Retrieve from cache (Cache HIT)
        hit_data = await aget_cached_list(payload_key)
        assert hit_data is not None
        assert hit_data["total"] == 1
        assert hit_data["data"][0]["name"] == "Demo Party"
        print("✅ Cached query retrieved successfully (Cache HIT).")

        # 3. Invalidate on mutation
        purged = await ainvalidate_model(Party)
        assert purged >= 2  # payload key + meta key
        assert payload_key not in fake_storage
        assert meta_key not in fake_storage
        print(f"✅ Invalidation successfully purged {purged} keys for model 'Party'.")


def main():
    test_configuration_defaults()
    test_key_generation_and_redisinsight_structure()
    asyncio.run(test_disabled_cache_bypass())
    asyncio.run(test_async_caching_and_invalidation_flow())
    print("\n🎉 ALL VALKEY CACHE TESTS PASSED SUCCESSFULLY!\n")


if __name__ == "__main__":
    main()

