"""Redis cache service."""

import json
from typing import Optional

import redis.asyncio as redis

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """Redis cache service for storing and retrieving cached data."""

    def __init__(self):
        """Initialize cache service."""
        self._client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        """
        Get or create Redis client.

        Returns:
            Redis client instance
        """
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Redis cache client initialized")
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value is not None:
                logger.debug(f"Cache hit: {key}")
            else:
                logger.debug(f"Cache miss: {key}")
            return value
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            ttl = ttl or settings.REDIS_CACHE_TTL
            await client.set(key, value, ex=ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            await client.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache for key {key}: {e}")
            return False

    async def get_json(self, key: str) -> Optional[dict]:
        """
        Get JSON value from cache.

        Args:
            key: Cache key

        Returns:
            Decoded JSON dict or None if not found
        """
        value = await self.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON for key {key}: {e}")
            return None

    async def set_json(self, key: str, value: dict, ttl: int = None) -> bool:
        """
        Set JSON value in cache.

        Args:
            key: Cache key
            value: Dict value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ttl)
        except Exception as e:
            logger.error(f"Error encoding JSON for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in cache.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New counter value
        """
        try:
            client = await self.get_client()
            return await client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing counter for key {key}: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            await client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis cache connection closed")


__all__ = ["CacheService"]
