"""Sets up the logging configuration for the Instalker application."""

import logging


def setup_logging() -> None:
    """
    Configure the logging system for the application.

    :param log_directory: Directory where the log file will be saved.
    :param log_filename: Name of the log file.
    """
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("instalker.log"),
            logging.StreamHandler(),
        ],
    )
