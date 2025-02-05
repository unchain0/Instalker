"""Handles the main functionality of the Instalker application.

Including image management and Instagram downloading tasks.
"""

import argparse
import logging
import os
from datetime import timedelta

from src.core.image_manager import ImageManager
from src.core.instagram import Instagram
from src.utils.logger import setup_logging


def prompt_yes_no(message: str) -> bool:
    """Prompts the user with a yes/no question and returns True for 'y'.

    Args:
        message (str): The message to display to the user.

    Returns:
        bool: True if the user answers 'y', False otherwise.

    """
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ("y", "n"):
            return response == "y"
        logging.info("Please answer with 'y' or 'n'.")


def get_usernames() -> set[str]:
    """Get usernames inputted by the user, separated by spaces.

    Returns:
        set[str]: The set of usernames.

    """
    users_input = input("Enter the username(s) separated by a space: ").strip()
    return set(users_input.split())


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.

    """
    parser = argparse.ArgumentParser(
        description="Automated Instagram profile downloader and image manager.",
    )
    parser.add_argument(
        "--min-width",
        type=int,
        help="Minimum width for images to keep (for removal of small images)",
    )
    parser.add_argument(
        "--min-height",
        type=int,
        help="Minimum height for images to keep (for removal of small images)",
    )
    parser.add_argument(
        "--remove-old",
        type=int,
        help="Remove images older than the specified number of days",
    )
    parser.add_argument(
        "--manual-users",
        action="store_true",
        help="Prompt for Instagram usernames input; else, TARGET_USERS will be used",
    )
    return parser.parse_args()


def handle_image_management(args: argparse.Namespace) -> None:
    """Handle image management tasks using CLI arguments or interactively."""
    image_manager = ImageManager()

    # Remove small images
    if args.min_width is not None and args.min_height is not None:
        image_manager.remove_small_images(min_size=(args.min_width, args.min_height))
    elif prompt_yes_no("Do you want to remove small images interactively?"):
        try:
            width = int(input("Enter the minimum width: "))
            height = int(input("Enter the minimum height: "))
        except ValueError:
            logging.exception("Invalid input. Please enter a number.")
        else:
            image_manager.remove_small_images(min_size=(width, height))

    # Remove old images
    if args.remove_old is not None:
        image_manager.remove_old_images(timedelta(days=args.remove_old))
    elif prompt_yes_no("Do you want to remove old images interactively?"):
        try:
            days = int(input("Enter the number of days: "))
        except ValueError:
            logging.exception("Invalid input. Please enter a number.")
        else:
            image_manager.remove_old_images(timedelta(days=days))


def handle_instagram_download(args: argparse.Namespace) -> None:
    """Handle Instagram downloading tasks using CLI arguments or interactively."""
    if args.manual_users:
        users = get_usernames()
        instagram = Instagram(users)
    else:
        instagram = Instagram(None)

    os.system("cls" if os.name == "nt" else "clear")
    instagram.run()


def main() -> None:
    """Initialize and run the application."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting the application")
    args = parse_arguments()

    handle_image_management(args)
    handle_instagram_download(args)


if __name__ == "__main__":
    main()
