"""Script to initialize the database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.database.session import init_db
from app.utils.logger import setup_logger, get_logger
from app.config import settings

# Setup logger
setup_logger(
    log_file=settings.LOG_FILE,
    log_level=settings.LOG_LEVEL,
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
)
logger = get_logger(__name__)


async def main():
    """Initialize database tables."""
    logger.info("Initializing database...")

    try:
        await init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
