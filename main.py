"""Initialize logging and run the Instagram class."""

from src.classes.instagram import Instagram
from src.logger_config import setup_logging


def main() -> None:
    """Set up logging and run the Instagram class."""
    setup_logging()
    ig = Instagram()
    ig.run(remove_old_images=True)


if __name__ == "__main__":
    main()
