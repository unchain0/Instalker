import logging

import src.constants as const


def setup_logging(log_filename: str = "instalker.log") -> None:
    """
    Configures the logging system for the application.

    :param log_directory: Directory where the log file will be saved.
    :param log_filename: Name of the log file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(const.LOG_DIRECTORY / log_filename),
        ],
    )
