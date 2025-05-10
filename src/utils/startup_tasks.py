"""Utility script for application startup tasks like DB init and initial import."""

import logging

from sqlalchemy import func, select

# Import necessary components from core
# Ensure correct path resolution if running standalone vs as module
try:
    from src.core.db import Profile, SessionLocal, init_db
    from src.core.import_users import import_users_from_json
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logging.error("Failed to import modules for startup tasks: %s", e)
    logging.error("Ensure script is run from project root or paths are correct.")
    raise SystemExit("Startup task module import failed.") from e

logger = logging.getLogger(__name__)


def run_startup_tasks() -> None:
    """Executes startup tasks: DB initialization and initial user import."""

    # 1. Initialize DB (create tables if they don't exist)
    try:
        init_db()
    except Exception as e:
        logger.error("Failed to initialize database: %s", e, exc_info=True)
        # Make this error fatal for startup
        raise SystemExit("Database initialization failed.") from e

    # 2. Check if DB is empty and import users if needed
    db_check_session = None
    try:
        db_check_session = SessionLocal()
        user_count_stmt = select(func.count()).select_from(Profile)
        user_count = db_check_session.scalars(user_count_stmt).one()

        if user_count == 0:
            logger.info(
                "Database appears empty. Attempting initial user import from JSON..."
            )
            # import_users_from_json handles its own session/transaction
            import_users_from_json()
            logger.info("Initial user import process completed.")
        else:
            logger.info(
                "Database contains %d users. Skipping initial JSON import.", user_count
            )

    except Exception as e:
        logger.error(
            "Failed during initial user import check/process: %s", e, exc_info=True
        )
        # Decide if this error should stop the application
        # For now, log the error and continue, but it might be better to stop:
        # raise SystemExit("Initial user import check/process failed.") from e
    finally:
        if db_check_session:
            db_check_session.close()


# Allow running startup tasks standalone if needed (for testing/manual init)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running startup tasks standalone...")
    try:
        run_startup_tasks()
        logger.info("Startup tasks completed successfully.")
    except Exception as e:
        logger.error("Standalone startup tasks failed: %s", e)
