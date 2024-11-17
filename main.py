import logging
import os

from src.core.image_manager import ImageManager
from src.core.instagram import Instagram
from src.utils.logger import setup_logging


def clear_console() -> None:
    """Clears the console based on the operating system."""
    os.system("cls" if os.name == "nt" else "clear")


def prompt_yes_no(message: str) -> bool:
    """Prompts the user with a yes/no question and returns True for 'y'."""
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ("y", "n"):
            return response == "y"
        print("Please answer with 'y' or 'n'.")


def get_usernames() -> set[str]:
    """Gets usernames inputted by the user, separated by spaces."""
    users_input = input("Enter the usernames separated by a space: ").strip()
    users = set(users_input.split())
    return users


def main() -> None:
    """
    Initialize and run the application.

    This function performs the following steps:
    1. Sets up logging for the application.
    2. Clears the console.
    3. Creates an instance of ImageManager and performs cleanup operations.
    4. Creates an instance of Instagram and runs the main process.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    clear_console()

    image_manager = ImageManager()

    if prompt_yes_no("Do you want to remove small images?"):
        image_manager.remove_small_images(min_size=(256, 256))

    if prompt_yes_no("Do you want to remove old images (more than 1 week)?"):
        image_manager.remove_old_images()

    if prompt_yes_no("Do you want to add users manually?"):
        users = get_usernames()
        instagram = Instagram(users)
    else:
        instagram = Instagram(None)

    logger.info("Starting the application")
    instagram.run()


if __name__ == "__main__":
    main()
