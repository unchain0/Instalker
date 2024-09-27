from src.classes.instagram import Instagram
from src.logger_config import setup_logging


def main() -> None:
    setup_logging()

    ig = Instagram()
    ig.run()


if __name__ == "__main__":
    main()
