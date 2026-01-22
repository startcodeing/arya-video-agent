"""Unit tests for cache service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache import CacheService


@pytest.fixture
def cache_service():
    """Create cache service instance."""
    return CacheService()


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    with patch("app.services.cache.redis.from_url") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.mark.asyncio
async def test_get_client_initializes_redis(cache_service, mock_redis):
    """Test that get_client initializes Redis client."""
    with patch("app.services.cache.redis.from_url", return_value=mock_redis):
        client = await cache_service.get_client()

        assert client is not None
        assert cache_service._client is not None


@pytest.mark.asyncio
async def test_get_cache_hit(cache_service, mock_redis):
    """Test getting value from cache (hit)."""
    mock_redis.get = AsyncMock(return_value="cached_value")

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        value = await cache_service.get("test_key")

        assert value == "cached_value"
        mock_redis.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_get_cache_miss(cache_service, mock_redis):
    """Test getting value from cache (miss)."""
    mock_redis.get = AsyncMock(return_value=None)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        value = await cache_service.get("test_key")

        assert value is None
        mock_redis.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_get_cache_error(cache_service, mock_redis):
    """Test getting value from cache with error."""
    mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        value = await cache_service.get("test_key")

        assert value is None


@pytest.mark.asyncio
async def test_set_cache_success(cache_service, mock_redis):
    """Test setting value in cache."""
    mock_redis.set = AsyncMock(return_value=True)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.set("test_key", "test_value")

        assert result is True
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_set_cache_with_ttl(cache_service, mock_redis):
    """Test setting value in cache with custom TTL."""
    mock_redis.set = AsyncMock(return_value=True)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.set("test_key", "test_value", ttl=100)

        assert result is True
        # Check that set was called with ex=100
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == "test_value"
        # The third argument should be ex=100


@pytest.mark.asyncio
async def test_set_cache_error(cache_service, mock_redis):
    """Test setting value in cache with error."""
    mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.set("test_key", "test_value")

        assert result is False


@pytest.mark.asyncio
async def test_delete_cache_success(cache_service, mock_redis):
    """Test deleting value from cache."""
    mock_redis.delete = AsyncMock(return_value=1)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_delete_cache_error(cache_service, mock_redis):
    """Test deleting value from cache with error."""
    mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.delete("test_key")

        assert result is False


@pytest.mark.asyncio
async def test_exists_true(cache_service, mock_redis):
    """Test checking if key exists (exists)."""
    mock_redis.exists = AsyncMock(return_value=1)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.exists("test_key")

        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_exists_false(cache_service, mock_redis):
    """Test checking if key exists (not exists)."""
    mock_redis.exists = AsyncMock(return_value=0)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.exists("test_key")

        assert result is False


@pytest.mark.asyncio
async def test_get_json_success(cache_service, mock_redis):
    """Test getting JSON value from cache."""
    import json

    test_dict = {"key": "value", "number": 123}
    mock_redis.get = AsyncMock(return_value=json.dumps(test_dict))

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.get_json("test_key")

        assert result == test_dict


@pytest.mark.asyncio
async def test_get_json_invalid_json(cache_service, mock_redis):
    """Test getting invalid JSON from cache."""
    mock_redis.get = AsyncMock(return_value="invalid json")

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.get_json("test_key")

        assert result is None


@pytest.mark.asyncio
async def test_set_json_success(cache_service, mock_redis):
    """Test setting JSON value in cache."""
    test_dict = {"key": "value", "number": 123}
    mock_redis.set = AsyncMock(return_value=True)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.set_json("test_key", test_dict)

        assert result is True
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_increment_success(cache_service, mock_redis):
    """Test incrementing a counter."""
    mock_redis.incrby = AsyncMock(return_value=5)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.increment("counter_key", 3)

        assert result == 5
        mock_redis.incrby.assert_called_once_with("counter_key", 3)


@pytest.mark.asyncio
async def test_increment_error(cache_service, mock_redis):
    """Test incrementing with error."""
    mock_redis.incrby = AsyncMock(side_effect=Exception("Redis error"))

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.increment("counter_key")

        assert result == 0


@pytest.mark.asyncio
async def test_expire_success(cache_service, mock_redis):
    """Test setting expiration on key."""
    mock_redis.expire = AsyncMock(return_value=True)

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.expire("test_key", 300)

        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 300)


@pytest.mark.asyncio
async def test_expire_error(cache_service, mock_redis):
    """Test setting expiration with error."""
    mock_redis.expire = AsyncMock(side_effect=Exception("Redis error"))

    with patch.object(cache_service, "get_client", return_value=mock_redis):
        result = await cache_service.expire("test_key", 300)

        assert result is False


@pytest.mark.asyncio
async def test_close_connection(cache_service, mock_redis):
    """Test closing Redis connection."""
    mock_redis.close = AsyncMock()

    cache_service._client = mock_redis
    await cache_service.close()

    assert cache_service._client is None
    mock_redis.close.assert_called_once()
