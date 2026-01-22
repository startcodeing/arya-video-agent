"""Script to start the Celery worker."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.utils.logger import setup_logger, get_logger

# Setup logger
setup_logger(
    log_file=settings.LOG_FILE,
    log_level=settings.LOG_LEVEL,
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
)
logger = get_logger(__name__)


def main():
    """Start the Celery worker."""
    logger.info("Starting Celery worker")

    import subprocess
    subprocess.run([
        "celery",
        "-A",
        "app.scheduler.celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=4",
    ])


if __name__ == "__main__":
    main()
