"""Initialize logging and run the Instagram class."""

import logging

from src.classes.image_manager import ImageManager
from src.classes.instagram import Instagram
from src.logger_config import setup_logging


def main() -> None:
    """Initialize and run the application.

    This function performs the following steps:
    1. Sets up logging for the application.
    2. Logs the start of the application.
    3. Initializes the download directory path.
    4. Creates an instance of ImageManager and removes old images.
    5. Creates an instance of Instagram and runs the application.

    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting the application")

    image_manager = ImageManager()
    image_manager.remove_old_images()

    instagram = Instagram()
    instagram.run()


if __name__ == "__main__":
    main()
