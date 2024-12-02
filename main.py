import logging
import os
from datetime import timedelta

from src.core.image_manager import ImageManager
from src.core.instagram import Instagram
from src.utils.logger import setup_logging


def prompt_yes_no(message: str) -> bool:
    """
    Prompts the user with a yes/no question and returns True for 'y'.

    Args:
        message (str): The message to display to the user.

    Returns:
        bool: True if the user answers 'y', False otherwise
    """
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ("y", "n"):
            return response == "y"
        print("Please answer with 'y' or 'n'.")


def get_usernames() -> set[str]:
    """
    Gets usernames inputted by the user, separated by spaces.

    Returns:
        set[str]: The set of usernames.
    """
    users_input = input("Enter the username(s) separated by a space: ").strip()
    users = set(users_input.split())
    return users


def handle_image_management() -> None:
    """
    Handle image management tasks.
    """
    image_manager = ImageManager()

    if prompt_yes_no("Do you want to remove small images?"):
        try:
            width = int(input("Enter the minimum width: "))
            height = int(input("Enter the minimum height: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            return

        min_size = (width, height)
        image_manager.remove_small_images(min_size=min_size)

    if prompt_yes_no("Do you want to remove old images?"):
        try:
            days = int(input("Enter the number of days: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            return

        image_manager.remove_old_images(timedelta(days=days))


def handle_instagram_download() -> None:
    """
    Handle Instagram downloading tasks.
    """
    if prompt_yes_no("Do you want to add users manually?"):
        users = get_usernames()
        instagram = Instagram(users)
    else:
        instagram = Instagram(None)

    os.system("cls" if os.name == "nt" else "clear")
    instagram.run()


def main() -> None:
    """
    Initialize and run the application.
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting the application")
    handle_image_management()
    handle_instagram_download()


if __name__ == "__main__":
    main()
