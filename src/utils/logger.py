"""Module that sets up logging for the Instalker application."""

import datetime
import logging
from logging import DEBUG, Formatter, StreamHandler, getLogger, root
from logging.handlers import TimedRotatingFileHandler
from sys import stdout
from typing import Optional

from src import LOG_DIRECTORY


def setup_logging(log_level: Optional[int] = None) -> logging.Logger:
    """Configure application logging with rotation and formatting.

    Args:
        log_level: Optional custom log level (defaults to DEBUG if None)

    Returns:
        The configured root logger
    """
    # Reset existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Log file path with timestamp
    timestamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime(
        "%Y-%m-%d"
    )
    log_file = LOG_DIRECTORY / f"instalker_{timestamp}.log"

    # Formatters
    file_formatter = Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # File handler with rotation
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        backupCount=14,  # Keep logs for 14 days
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(DEBUG)

    # Console handler
    console_handler = StreamHandler(stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Root logger configuration
    root_logger = getLogger()
    root_logger.setLevel(log_level or DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress external library logs using fully-qualified logging levels
    getLogger("urllib3").setLevel(logging.WARNING)
    getLogger("instaloader").setLevel(logging.INFO)
    getLogger("PIL").setLevel(logging.INFO)

    return root_logger
