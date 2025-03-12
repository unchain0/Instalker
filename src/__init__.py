"""Initialize settings for the Instalker application."""

from .config.settings import (
    DOWNLOAD_DIRECTORY,
    LATEST_STAMPS,
    LOG_DIRECTORY,
    SOURCE_DIRECTORY,
    TARGET_USERS,
)

__all__ = [
    "DOWNLOAD_DIRECTORY",
    "LATEST_STAMPS",
    "LOG_DIRECTORY",
    "SOURCE_DIRECTORY",
    "TARGET_USERS",
]
