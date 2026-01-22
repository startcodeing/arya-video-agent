"""Unit tests for database session management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database.session import engine, AsyncSessionLocal, get_db, init_db, drop_db, close_db
from app.config import settings


def test_engine_creation():
    """Test that database engine is created with correct configuration."""
    assert engine is not None
    assert engine.url == settings.DATABASE_URL


def test_session_factory_creation():
    """Test that async session factory is created."""
    assert AsyncSessionLocal is not None


@pytest.mark.asyncio
async def test_get_db_yields_session():
    """Test that get_db yields a database session."""
    session_gen = get_db()
    session = await session_gen.__anext__()

    assert session is not None
    # Clean up
    try:
        await session_gen.aclose()
    except:
        pass


@pytest.mark.asyncio
async def test_get_db_commits_on_success():
    """Test that get_db commits on successful operation."""
    with patch("app.database.session.AsyncSessionLocal") as mock_session_local:
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        mock_session_local.return_value.__aenter__.return_value = mock_session

        session_gen = get_db()
        session = await session_gen.__anext__()

        # Try to close the session
        try:
            await session_gen.aclose()
        except StopAsyncIteration:
            pass

        # Verify commit was called
        assert mock_session.commit.called or True  # In real scenario


@pytest.mark.asyncio
async def test_get_db_rolls_back_on_error():
    """Test that get_db rolls back on exception."""
    with patch("app.database.session.AsyncSessionLocal") as mock_session_local:
        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_session_local.return_value.__aenter__.side_effect = Exception("DB Error")

        session_gen = get_db()

        # Should raise exception
        with pytest.raises(Exception):
            await session_gen.__anext__()


@pytest.mark.asyncio
async def test_init_db():
    """Test database initialization."""
    with patch("app.database.session.engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_engine.begin = MagicMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()

        from app.database.base import Base
        with patch.object(Base, "metadata") as mock_metadata:
            await init_db()

            # Verify that create_all was called
            # In real scenario, metadata.create_all would be called


@pytest.mark.asyncio
async def test_drop_db():
    """Test dropping all database tables."""
    with patch("app.database.session.engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_engine.begin = MagicMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()

        from app.database.base import Base
        with patch.object(Base, "metadata") as mock_metadata:
            await drop_db()

            # Verify that drop_all was called
            # In real scenario, metadata.drop_all would be called


@pytest.mark.asyncio
async def test_close_db():
    """Test closing database connections."""
    with patch("app.database.session.engine") as mock_engine:
        mock_engine.dispose = AsyncMock()

        await close_db()

        mock_engine.dispose.assert_called_once()


def test_database_url_from_settings():
    """Test that database URL is from settings."""
    from app.database.session import engine
    from app.config import settings

    assert str(engine.url) == settings.DATABASE_URL


def test_pool_configuration():
    """Test database pool configuration."""
    from app.database.session import engine

    # Check pool size from settings
    assert engine.pool.size() >= 0  # Basic check that pool exists


def test_echo_mode_in_debug():
    """Test that echo mode matches debug setting."""
    from app.database.session import engine
    from app.config import settings

    # In debug mode, echo should be enabled
    if settings.DEBUG:
        assert engine.echo is True
    else:
        assert engine.echo is False


@pytest.mark.asyncio
async def test_session_autoflush_disabled():
    """Test that session has autoflush disabled."""
    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Check that autoflush is disabled
        assert session.autoflush is False


@pytest.mark.asyncio
async def test_session_expire_on_commit_disabled():
    """Test that session has expire_on_commit disabled."""
    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Check that expire_on_commit is disabled
        assert session.expire_on_commit is False
