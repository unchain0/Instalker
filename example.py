"""Example script demonstrating usage of the Instalker components."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta

from sqlalchemy.orm import Session

from src.core.db import SessionLocal  # Need SessionLocal for session management
from src.core.file_manager import FileManager
from src.core.instagram import Instagram
from src.utils.logger import setup_logging
from src.utils.startup_tasks import run_startup_tasks  # Import startup tasks

logger = logging.getLogger(__name__)  # Get logger for example script


# Context manager for DB session (copied from main.py for demonstration)
@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        # Let operations within the context manage commit/rollback
    except Exception:
        logger.exception("Session error occurred. Rolling back.")
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    """Entry point for the example application.

    This function demonstrates:
    1. Running file management tasks.
    2. Running the main Instagram processing with DB integration.
    """
    # --- File Management ---
    logger.info("Running file management tasks...")
    file_manager = FileManager()
    file_manager.remove_old_files(cutoff_delta=timedelta(days=30))
    logger.info("File management tasks completed.")

    # --- Instagram Processing ---
    logger.info("Starting Instagram processing...")
    try:
        with get_session() as main_db_session:
            instagram = Instagram(
                db=main_db_session,
                highlights=False,
                target_users="all",
            )
            instagram.run()
        logger.info("Instagram processing finished successfully.")
    except Exception as e:
        logger.error(
            "An error occurred during Instagram processing: %s", e, exc_info=True
        )
        # Decide how to handle errors in the example (e.g., re-raise, log only)


if __name__ == "__main__":
    # 1. Setup Logging
    setup_logging()

    # 2. Run Startup Tasks (DB Init, Conditional Import)
    logger.info("Running startup tasks...")
    try:
        run_startup_tasks()
    except SystemExit as e:
        logger.critical("Startup tasks failed critically. Exiting. Error: %s", e)
        exit(1)
    except Exception as e:
        logger.critical(
            "An unexpected critical error during startup tasks. Exiting. Error: %s",
            e,
            exc_info=True,
        )
        exit(1)
    logger.info("Startup tasks completed.")

    # 3. Run Main Application Logic Example
    main()
