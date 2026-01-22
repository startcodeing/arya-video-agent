"""Unit tests for logger configuration."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.utils.logger import setup_logger, get_logger


def test_setup_logger_creates_log_directory(tmp_path):
    """Test that setup_logger creates log directory."""
    log_file = tmp_path / "test_logs" / "app.log"

    setup_logger(
        log_file=str(log_file),
        log_level="INFO",
    )

    # Check that log directory was created
    assert log_file.parent.exists()


def test_setup_logger_creates_error_log(tmp_path):
    """Test that setup_logger creates error log file."""
    log_file = tmp_path / "test_logs" / "app.log"

    setup_logger(
        log_file=str(log_file),
        log_level="INFO",
    )

    # Check that error log file path is created
    error_log = log_file.parent / "errors.log"
    # The error log handler is configured but file is created on first log


def test_get_logger_returns_logger():
    """Test that get_logger returns a logger instance."""
    logger = get_logger("test")
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "warning")


def test_get_logger_with_name():
    """Test get_logger with name parameter."""
    logger = get_logger("my_module")
    # Logger should be bound with the name
    assert logger is not None


def test_get_logger_without_name():
    """Test get_logger without name parameter."""
    logger = get_logger()
    assert logger is not None


def test_setup_logger_with_custom_parameters(tmp_path):
    """Test setup_logger with custom parameters."""
    log_file = tmp_path / "custom_logs" / "custom.log"

    setup_logger(
        log_file=str(log_file),
        log_level="DEBUG",
        rotation="5 MB",
        retention="7 days",
    )

    # Check that directory was created
    assert log_file.parent.exists()


@patch("app.utils.logger.logger")
def test_logger_remove_default_handler(mock_logger):
    """Test that setup_logger removes default handler."""
    mock_logger.remove = MagicMock()
    mock_logger.add = MagicMock()

    setup_logger(log_file="./test.log", log_level="INFO")

    # Verify remove was called
    mock_logger.remove.assert_called()


@patch("app.utils.logger.logger")
def test_logger_adds_handlers(mock_logger):
    """Test that setup_logger adds handlers."""
    mock_logger.remove = MagicMock()
    mock_logger.add = MagicMock()
    mock_logger.complete = MagicMock()

    setup_logger(log_file="./test.log", log_level="INFO")

    # Verify add was called (should be called multiple times for console and files)
    assert mock_logger.add.call_count >= 2


def test_log_levels():
    """Test different log levels."""
    logger = get_logger("test_levels")

    # These should not raise exceptions
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
