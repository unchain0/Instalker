from datetime import timedelta

from src import FileManager, Instagram, get_session, setup_logging


def main() -> None:
    """Entry point for the application's main processing loop."""

    try:
        with get_session() as main_db_session:
            fm = FileManager()
            fm.remove_old_files(cutoff_delta=timedelta(days=15))

            instagram = Instagram(
                db=main_db_session,
                highlights=False,
            )
            instagram.run()
        logger.info("Instagram processing finished successfully.")
    except (ConnectionError, TimeoutError):
        logger.exception("Network error during Instagram processing")
    except ValueError:
        logger.exception("Invalid data encountered during Instagram processing")
    except RuntimeError:
        logger.exception("Runtime error during Instagram processing")


if __name__ == "__main__":
    # Copy and paste this file into a new file called `main.py`.
    logger = setup_logging()
    main()
