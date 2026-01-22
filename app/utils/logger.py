"""Logging configuration for the application."""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    log_file: str = "./logs/app.log",
    log_level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "30 days",
) -> None:
    """
    Configure application logger using Loguru.

    Args:
        log_file: Path to log file
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: Log rotation settings
        retention: Log retention settings
    """
    # Remove default handler
    logger.remove()

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Add console handler with colored output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Add file handler for all logs
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression="zip",
        encoding="utf-8",
    )

    # Add separate error log file
    error_log = log_path.parent / "errors.log"
    logger.add(
        error_log,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=rotation,
        retention=retention,
        compression="zip",
        encoding="utf-8",
    )


def get_logger(name: str = None):
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Loguru logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger


__all__ = ["setup_logger", "get_logger", "logger"]
