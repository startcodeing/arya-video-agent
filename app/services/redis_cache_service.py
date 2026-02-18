"""Redis cache service with connection pooling and performance monitoring."""

import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool
from redis.asyncio.retry import Retry

from app.config import settings
from app.services.cache_config import (
    CacheNamespace,
    CacheVersion,
    CacheTTL,
    CacheKeyGenerator,
    CacheConfig,
    CacheMetadata,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RedisCacheService:
    """
    Redis cache service with connection pooling and performance monitoring.

    Features:
    - Connection pooling
    - Automatic retry on failure
    - Cache metadata tracking
    - Performance monitoring (hit rate, miss rate, latency)
    - Namespace-based key organization
    - TTL management
    - Cache invalidation
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
    ):
        """
        Initialize Redis cache service.

        Args:
            redis_url: Redis connection URL (default: from settings)
            max_connections: Maximum number of connections in pool
            socket_timeout: Timeout for socket operations
            socket_connect_timeout: Timeout for socket connection
            retry_on_timeout: Retry on timeout
            health_check_interval: Health check interval in seconds
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval

        # Performance metrics
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_errors = 0
        self.latency_samples = []

        # Redis connection pool
        self._pool = None
        self._redis = None

        # Cache metadata registry
        self._cache_metadata: Dict[str, CacheMetadata] = {}

    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                health_check_interval=self.health_check_interval,
                decode_responses=True,  # Automatically decode JSON responses
            )

            # Create Redis client with retry logic
            self._redis = aioredis.Redis(
                connection_pool=self._pool,
                retry=Retry(ExponentialBackoff(cap=3, base=1), 3),
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
            )

            # Test connection
            await self._redis.ping()
            logger.info("Redis cache service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis cache service: {str(e)}")
            raise

    async def close(self):
        """Close Redis connection pool."""
        if self._pool:
            await self._pool.disconnect()
            logger.info("Redis cache service connection pool closed")

    async def ping(self) -> bool:
        """
        Ping Redis server.

        Returns:
            True if Redis is responsive, False otherwise
        """
        try:
            result = await self._redis.ping()
            return result
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False

    async def get(
        self,
        key: str,
        default: Optional[Any] = None
        namespace: Optional[CacheNamespace] = None,
    ) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found
            namespace: Cache namespace (for metadata tracking)

        Returns:
            Cached value or default
        """
        start_time = time.perf_counter()
        self.total_requests += 1

        try:
            # Get value from Redis
            value = await self._redis.get(key)

            if value is None:
                self.cache_misses += 1
                logger.debug(f"Cache miss: {key}")
                return default

            # Decode JSON
            if isinstance(value, (str, bytes)):
                try:
                    value = json.loads(value) if isinstance(value, str) else value.decode('utf-8')
                except json.JSONDecodeError:
                    logger.debug(f"Value is not JSON, returning as-is: {key}")
                    # Return as-is if not JSON

            self.cache_hits += 1
            logger.debug(f"Cache hit: {key}")

            # Record latency
            latency = time.perf_counter() - start_time
            self._record_latency(latency)

            # Update metadata if namespace provided
            if namespace and key in self._cache_metadata:
                self._cache_metadata[key].record_hit()

            return value

        except Exception as e:
            self.total_errors += 1
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: Optional[CacheNamespace] = None,
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: from namespace TTL)
            namespace: Cache namespace (for metadata tracking)

        Returns:
            True if successful, False otherwise
        """
        start_time = time.perf_counter()

        try:
            # Serialize value to JSON
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value, ensure_ascii=False, default=str)

            # Get TTL from namespace if not provided
            if ttl is None and namespace:
                ttl = CacheConfig.get_ttl(namespace)

            # Set value in Redis
            if ttl:
                await self._redis.setex(key, ttl, value)
            else:
                await self._redis.set(key, value)

            logger.debug(f"Cache set: {key} (TTL: {ttl or 'default'})")

            # Create metadata
            if namespace:
                metadata = CacheMetadata(
                    created_at=datetime.utcnow(),
                    ttl=ttl or CacheConfig.DEFAULT_TTL,
                    key=key,
                    value_type=type(value).__name__,
                )
                self._cache_metadata[key] = metadata

            # Record latency
            latency = time.perf_counter() - start_time
            self._record_latency(latency)

            return True

        except Exception as e:
            self.total_errors += 1
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        start_time = time.perf_counter()

        try:
            # Delete from Redis
            await self._redis.delete(key)
            logger.debug(f"Cache delete: {key}")

            # Remove metadata
            if key in self._cache_metadata:
                del self._cache_metadata[key]

            # Record latency
            latency = time.perf_counter() - start_time
            self._record_latency(latency)

            return True

        except Exception as e:
            self.total_errors += 1
            logger.error(f"Cache delete error for key {key}: {str(e)}")
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
            result = await self._redis.exists(key)
            return result == 1
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for existing key.

        Args:
            key: Cache key
            ttl: New TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        start_time = time.perf_counter()

        try:
            # Set expiration
            result = await self._redis.expire(key, ttl)
            logger.debug(f"Cache expire: {key} (TTL: {ttl}s)")

            # Update metadata if exists
            if key in self._cache_metadata:
                metadata = self._cache_metadata[key]
                metadata.expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                metadata.ttl = ttl
                self._cache_metadata[key] = metadata

            # Record latency
            latency = time.perf_counter() - start_time
            self._record_latency(latency)

            return result

        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False

    async def increment(
        self,
        key: str,
        amount: int = 1
        default: int = 0
    ) -> int:
        """
        Increment numeric value in cache.

        Args:
            key: Cache key
            amount: Increment amount
            default: Default value if key doesn't exist

        Returns:
            Incremented value
        """
        try:
            # Increment value
            value = await self._redis.incrby(key, amount)

            # Return value
            return value

        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return default

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache (mget operation).

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key -> value
        """
        start_time = time.perf_counter()

        try:
            # Get all values
            values = await self._redis.mget(keys)

            # Deserialize JSON values
            result = {}
            for key, value in zip(keys, values):
                if value is None:
                    self.cache_misses += 1
                    continue

                # Deserialize JSON
                if isinstance(value, (str, bytes)):
                    try:
                        value = json.loads(value) if isinstance(value, str) else value.decode('utf-8')
                    except json.JSONDecodeError:
                        logger.debug(f"Value is not JSON for key {key}")
                        value = value if isinstance(value, str) else value.decode('utf-8')

                self.cache_hits += 1
                result[key] = value

            # Record latency
            latency = time.perf_counter() - start_time
            self._record_latency(latency)

            logger.debug(f"Cache mget: {len(keys)} keys, {len(result)} hits")
            return result

        except Exception as e:
            self.total_errors += 1
            logger.error(f"Cache mget error: {str(e)}")
            return {}

    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set multiple values in cache (mset operation).

        Args:
            mapping: Dictionary of key -> value
            ttl: Time-to-live for all keys (default: MEDIUM TTL)

        Returns:
            True if successful, False otherwise
        """
        start_time = time.perf_counter()

        try:
            # Serialize values to JSON
            mapping_serialized = {}
            for key, value in mapping.items():
                if not isinstance(value, (str, bytes)):
                    value = json.dumps(value, ensure_ascii=False, default=str)
                mapping_serialized[key] = value

            # Set all values
            if ttl:
                # Use pipeline for atomic set with TTL
                async with self._redis.pipeline() as pipe:
                    for key, value in mapping_serialized.items():
                        pipe.setex(key, ttl, value)
                    await pipe.execute()
            else:
                # Use mset for faster bulk set
                await self._redis.mset(mapping_serialized)

            # Create metadata for all keys
            for key in mapping_serialized.keys():
                metadata = CacheMetadata(
                    created_at=datetime.utcnow(),
                    ttl=ttl or CacheConfig.DEFAULT_TTL,
                    key=key,
                    value_type=type(mapping[key]).__name__,
                )
                self._cache_metadata[key] = metadata

            # Record latency
            latency = time.perf_counter() - start_time
            self._record_latency(latency)

            logger.debug(f"Cache mset: {len(mapping)} keys (TTL: {ttl or 'default'})")
            return True

        except Exception as e:
            self.total_errors += 1
            logger.error(f"Cache mset error: {str(e)}")
            return False

    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple keys from cache.

        Args:
            keys: List of cache keys to delete

        Returns:
            Number of keys deleted
        """
        start_time = time.perf_counter()

        try:
            # Delete all keys
            result = await self._redis.delete(*keys)

            # Remove metadata for deleted keys
            for key in keys:
                if key in self._cache_metadata:
                    del self._cache_metadata[key]

            # Record latency
            latency = time.perf_counter() - start_time
            self._record_latency(latency)

            logger.debug(f"Cache delete: {len(keys)} keys")
            return result

        except Exception as e:
            self.total_errors += 1
            logger.error(f"Cache delete many error: {str(e)}")
            return 0

    async def invalidate_prefix(self, prefix: str) -> int:
        """
        Invalidate all cache keys with given prefix.

        Args:
            prefix: Cache key prefix

        Returns:
            Number of keys invalidated
        """
        start_time = time.perf_counter()

        try:
            # Find all keys with prefix
            keys = []
            async for key in self._redis.iscan(match=f"*{prefix}*"):
                keys.append(key)

            # Delete all keys
            if keys:
                result = await self.delete_many(keys)
            else:
                result = 0

            # Remove metadata
            keys_to_remove = [k for k in self._cache_metadata.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._cache_metadata[key]

            # Record latency
            latency = time.perf_counter() - start_time
            self._record_latency(latency)

            logger.info(f"Invalidated {result} keys with prefix {prefix}")
            return result

        except Exception as e:
            self.total_errors += 1
            logger.error(f"Cache invalidate prefix error for prefix {prefix}: {str(e)}")
            return 0

    async def clear_all(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        try:
            await self._redis.flushdb()
            logger.info("Flushed all cache entries")

            # Clear metadata
            self._cache_metadata.clear()

            # Reset metrics
            self.total_requests = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.total_errors = 0
            self.latency_samples = []

            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            # Get Redis info
            info = await self._redis.info()

            # Calculate hit rate
            total_requests = self.total_requests
            hit_rate = 0.0
            if total_requests > 0:
                hit_rate = self.cache_hits / total_requests

            # Calculate miss rate
            miss_rate = 1.0 - hit_rate

            # Calculate average latency
            avg_latency = 0.0
            if self.latency_samples:
                avg_latency = sum(self.latency_samples) / len(self.latency_samples)

            # Calculate error rate
            error_rate = 0.0
            if total_requests > 0:
                error_rate = self.total_errors / total_requests

            return {
                "total_requests": total_requests,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": round(hit_rate * 100, 2),
                "miss_rate": round(miss_rate * 100, 2),
                "error_rate": round(error_rate * 100, 2),
                "avg_latency_ms": round(avg_latency * 1000, 2),
                "total_errors": self.total_errors,
                "redis_connected_clients": info.get('connected_clients', 0),
                "redis_used_memory": info.get('used_memory', 0),
                "redis_used_memory_human": info.get('used_memory_human', '0B'),
                "redis_used_memory_peak": info.get('used_memory_peak', 0),
                "redis_keyspace_hits": info.get('keyspace_hits', 0),
                "redis_keyspace_misses": info.get('keyspace_misses', 0),
                "cache_size": len(self._cache_metadata),
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {
                "total_requests": self.total_requests,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": 0.0,
                "miss_rate": 0.0,
                "error_rate": 0.0,
                "avg_latency_ms": 0.0,
                "total_errors": self.total_errors,
                "cache_size": len(self._cache_metadata),
            }

    async def get_cache_metadata(self) -> List[Dict[str, Any]]:
        """
        Get all cache metadata.

        Returns:
            List of cache metadata dictionaries
        """
        metadata_list = []
        for key, metadata in self._cache_metadata.items():
            metadata_dict = metadata.to_dict()
            metadata_dict["is_expired"] = metadata.is_expired()
            metadata_list.append(metadata_dict)

        return metadata_list

    # ============================================================================
    # Private Methods
    # ============================================================================

    def _record_latency(self, latency: float) -> None:
        """Record latency sample."""
        self.latency_samples.append(latency)

        # Keep only last 1000 samples
        if len(self.latency_samples) > 1000:
            self.latency_samples.pop(0)

    async def _execute_redis_command(self, command: str, *args) -> Any:
        """
        Execute a Redis command.

        Args:
            command: Redis command
            args: Command arguments

        Returns:
            Command result
        """
        try:
            method = getattr(self._redis, command)
            return await method(*args)
        except Exception as e:
            logger.error(f"Redis command error: {command} {args}: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis.

        Returns:
            Health check result dictionary
        """
        try:
            # Ping Redis
            ping_result = await self.ping()
            is_healthy = ping_result

            # Get stats
            stats = await self.get_stats()

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "is_connected": is_healthy,
                "cache_size": stats.get("cache_size", 0),
                "hit_rate": stats.get("hit_rate", 0.0),
                "avg_latency_ms": stats.get("avg_latency_ms", 0.0),
                "connected_clients": stats.get("redis_connected_clients", 0),
                "used_memory": stats.get("redis_used_memory_human", "0B"),
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "is_connected": False,
                "error": str(e),
            }
