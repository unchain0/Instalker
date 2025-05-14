import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta

from sqlalchemy.orm import Session

from src.core.db import SessionLocal
from src.core.file_manager import FileManager
from src.core.instagram import Instagram
from src.utils.startup_tasks import run_startup_tasks

logger = logging.getLogger(__name__)


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations for the main loop."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.exception("Main processing session error occurred. Rolling back.")
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    """Entry point for the application's main processing loop."""

    # --- Run the main Instagram processing loop ---
    logger.info("Starting main Instagram processing...")
    try:
        with get_session() as main_db_session:
            fm = FileManager()
            fm.remove_old_files(cutoff_delta=timedelta(days=15))

            instagram = Instagram(
                db=main_db_session,
                highlights=False,
                target_users="all",
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
    # Copy and paste the above code into a new file named `main.py`.
    run_startup_tasks()
    main()
