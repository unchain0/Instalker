import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from src import LOG_DIRECTORY


def setup_logging() -> None:
    """
    Configure application logging with rotation and formatting.
    """
    # Reset existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Log file path with timestamp
    log_file = LOG_DIRECTORY / f"instalker_{datetime.now():%Y-%m-%d}.log"

    # Formatters
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
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
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress external library logs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("instaloader").setLevel(logging.INFO)
    logging.getLogger("PIL").setLevel(logging.INFO)
