"""Module for managing Instagram highlights and image management."""

import logging
from datetime import timedelta

from src.core.file_manager import FileManager
from src.core.instagram import Instagram
from src.utils.logger import setup_logging


def main() -> None:
    """Entry point for the program."""
    file_manager = FileManager()
    file_manager.remove_small_files(min_size=(256, 256))
    file_manager.remove_old_files(cutoff_delta=timedelta(days=365))

    instagram = Instagram(highlights=False)
    instagram.run()


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    main()
