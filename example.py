"""Module for managing Instagram highlights and image management."""

from datetime import timedelta

from src.core.file_manager import FileManager
from src.core.instagram import Instagram
from src.utils.logger import setup_logging


def main() -> None:
    """Entry point for the application.

    This function performs the following operations:
    1. Initializes a FileManager and uses it to:
        - Remove files smaller than 256x256 pixels
        - Remove files older than 365 days
    2. Initializes Instagram client with highlights disabled
    3. Executes the Instagram client
    """
    file_manager = FileManager()
    file_manager.remove_small_images(min_size=(256, 256))
    file_manager.remove_old_files(cutoff_delta=timedelta(days=365))

    instagram = Instagram(highlights=False, target_users="all")
    instagram.run()


if __name__ == "__main__":
    setup_logging()
    main()
