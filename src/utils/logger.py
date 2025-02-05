"""Module that sets up logging for the Instalker application."""

import datetime
import logging
from logging import DEBUG, Formatter, StreamHandler, getLogger, root
from logging.handlers import RotatingFileHandler
from sys import stdout

from src import LOG_DIRECTORY


def setup_logging() -> None:
    """Configure application logging with rotation and formatting."""
    # Reset existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Log file path with timestamp
    log_file = (
        LOG_DIRECTORY
        / f"instalker_{datetime.datetime.now(tz=datetime.UTC):%Y-%m-%d}.log"
    )

    # Formatters
    file_formatter = Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
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
    root_logger.setLevel(DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress external library logs using fully-qualified logging levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("instaloader").setLevel(logging.INFO)
    logging.getLogger("PIL").setLevel(logging.INFO)
