import logging
import os

from src.core.image_manager import ImageManager
from src.core.instagram import Instagram
from src.utils.logger import setup_logging


def main() -> None:
    """
    Initialize and run the application.

    This function performs the following steps:
    1. Sets up logging for the application.
    2. Logs the start of the application.
    3. Initializes the download directory path.
    4. Creates an instance of ImageManager and removes old images.
    5. Creates an instance of Instagram and runs the application.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    os.system("cls")

    image_manager = ImageManager()

    if input("Do you want to remove small images? (y/n): ").lower() == "y":
        image_manager.remove_small_images(min_size=(256, 256))

    if input("Do you want to remove old images? (y/n): ").lower() == "y":
        image_manager.remove_old_images()

    if input("Do you want to add users manually? (y/n): ").lower() == "y":
        users = input("Enter the usernames separated by a space: ").split()
        instagram = Instagram(set(users))
    else:
        instagram = Instagram(None)

    logger.info("Starting the application")
    instagram.run()


if __name__ == "__main__":
    main()
