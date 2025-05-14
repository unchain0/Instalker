import logging

from sqlalchemy import func, select

from src.core.db import Profile, SessionLocal, init_db
from src.utils.import_users import UserImporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
user_importer = UserImporter()


def run_startup_tasks() -> None:
    """Executes startup tasks: DB initialization and initial user import."""

    # 1. Initialize DB (create tables if they don't exist)
    try:
        init_db()
    except Exception:
        logger.exception("Failed to initialize database")

    # 2. Check if DB is empty and import users if needed
    db_check_session = None
    try:
        db_check_session = SessionLocal()
        user_count_stmt = select(func.count()).select_from(Profile)
        user_count = db_check_session.scalars(user_count_stmt).one()

        if user_count == 0:
            logger.info("Database appears empty. Attempting initial user import from JSON...")
            user_importer.execute_import()
            logger.info("Initial user import process completed.")
        else:
            logger.info("Database contains %d users. Skipping initial JSON import.", user_count)

    except Exception:
        logger.exception("Failed during initial user import check/process")
    finally:
        if db_check_session:
            db_check_session.close()


# Allow running startup tasks standalone if needed (for testing/manual init)
if __name__ == "__main__":
    logger.info("Running startup tasks standalone...")
    try:
        run_startup_tasks()
        logger.info("Startup tasks completed successfully.")
    except Exception:
        logger.exception("Standalone startup tasks failed")
