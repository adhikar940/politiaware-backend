"""
Custom Django Cache Backend powered exclusively by the official Valkey client (valkey-py).
Provides both synchronous and native asynchronous cache operations (aget, aset, adelete, atouch, aclear).
Does NOT require or import the redis package.
"""

import logging
import pickle
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from django.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT
except ImportError:
    class BaseCache:
        def __init__(self, params):
            self.key_prefix = params.get("KEY_PREFIX", "")
            self.default_timeout = params.get("TIMEOUT", 3600)
    DEFAULT_TIMEOUT = object()

try:
    import valkey
    import valkey.asyncio as aiovalkey
    HAS_VALKEY = True
except ImportError:
    valkey = None
    aiovalkey = None
    HAS_VALKEY = False


class ValkeyCache(BaseCache):
    """
    Django Cache Backend using the official Valkey library.
    Supports both sync and async Django cache APIs.
    """

    def __init__(self, server, params):
        super().__init__(params)
        self._server = server
        self._sync_client = None
        self._async_client = None

    def _get_sync_client(self):
        if self._sync_client is None and HAS_VALKEY:
            try:
                self._sync_client = valkey.from_url(
                    self._server,
                    encoding="utf-8",
                    decode_responses=False,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                )
            except Exception as exc:
                logger.error("Failed to connect sync Valkey client: %s", exc)
                return None
        return self._sync_client

    def _get_async_client(self):
        if self._async_client is None and HAS_VALKEY:
            try:
                self._async_client = aiovalkey.from_url(
                    self._server,
                    encoding="utf-8",
                    decode_responses=False,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                )
            except Exception as exc:
                logger.error("Failed to connect async Valkey client: %s", exc)
                return None
        return self._async_client

    def make_key(self, key, version=None):
        if self.key_prefix:
            return f"{self.key_prefix}:{key}"
        return str(key)

    def _get_timeout(self, timeout):
        if timeout == DEFAULT_TIMEOUT:
            return self.default_timeout
        return timeout

    # -----------------------------------------------------------------------
    # SYNCHRONOUS OPERATIONS
    # -----------------------------------------------------------------------

    def get(self, key: str, default: Any = None, version: Optional[int] = None) -> Any:
        client = self._get_sync_client()
        if not client:
            return default
        try:
            val = client.get(self.make_key(key, version=version))
            if val is not None:
                return pickle.loads(val)
        except Exception as exc:
            logger.error("Valkey sync get error for key '%s': %s", key, exc)
            return default
        return default

    def set(self, key: str, value: Any, timeout: Any = DEFAULT_TIMEOUT, version: Optional[int] = None) -> None:
        client = self._get_sync_client()
        if not client:
            return
        try:
            t = self._get_timeout(timeout)
            client.set(self.make_key(key, version=version), pickle.dumps(value), ex=t)
        except Exception as exc:
            logger.error("Valkey sync set error for key '%s': %s", key, exc)

    def delete(self, key: str, version: Optional[int] = None) -> bool:
        client = self._get_sync_client()
        if not client:
            return False
        try:
            return bool(client.delete(self.make_key(key, version=version)))
        except Exception as exc:
            logger.error("Valkey sync delete error for key '%s': %s", key, exc)
            return False

    def touch(self, key: str, timeout: Any = DEFAULT_TIMEOUT, version: Optional[int] = None) -> bool:
        client = self._get_sync_client()
        if not client:
            return False
        try:
            t = self._get_timeout(timeout)
            return bool(client.expire(self.make_key(key, version=version), t))
        except Exception as exc:
            logger.error("Valkey sync touch error for key '%s': %s", key, exc)
            return False

    def clear(self) -> None:
        client = self._get_sync_client()
        if not client:
            return
        try:
            client.flushdb()
        except Exception as exc:
            logger.error("Valkey sync clear error: %s", exc)

    # -----------------------------------------------------------------------
    # ASYNCHRONOUS OPERATIONS (Django 4.1+)
    # -----------------------------------------------------------------------

    async def aget(self, key: str, default: Any = None, version: Optional[int] = None) -> Any:
        client = self._get_async_client()
        if not client:
            return default
        try:
            val = await client.get(self.make_key(key, version=version))
            if val is not None:
                return pickle.loads(val)
        except Exception as exc:
            logger.error("Valkey async aget error for key '%s': %s", key, exc)
            return default
        return default

    async def aset(self, key: str, value: Any, timeout: Any = DEFAULT_TIMEOUT, version: Optional[int] = None) -> None:
        client = self._get_async_client()
        if not client:
            return
        try:
            t = self._get_timeout(timeout)
            await client.set(self.make_key(key, version=version), pickle.dumps(value), ex=t)
        except Exception as exc:
            logger.error("Valkey async aset error for key '%s': %s", key, exc)

    async def adelete(self, key: str, version: Optional[int] = None) -> bool:
        client = self._get_async_client()
        if not client:
            return False
        try:
            return bool(await client.delete(self.make_key(key, version=version)))
        except Exception as exc:
            logger.error("Valkey async adelete error for key '%s': %s", key, exc)
            return False

    async def atouch(self, key: str, timeout: Any = DEFAULT_TIMEOUT, version: Optional[int] = None) -> bool:
        client = self._get_async_client()
        if not client:
            return False
        try:
            t = self._get_timeout(timeout)
            return bool(await client.expire(self.make_key(key, version=version), t))
        except Exception as exc:
            logger.error("Valkey async atouch error for key '%s': %s", key, exc)
            return False

    async def aclear(self) -> None:
        client = self._get_async_client()
        if not client:
            return
        try:
            await client.flushdb()
        except Exception as exc:
            logger.error("Valkey async aclear error: %s", exc)


