"""Utility script to import users from JSON files into the database."""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# Setup basic logging for the script
# Note: This script's logger might conflict if run alongside main app.
# Consider passing logger or using a unique name if run concurrently.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    # Adjust relative paths if necessary after moving
    from src.config.settings import RESOURCES_DIRECTORY
    from src.core.db import Profile as DbProfile
    from src.core.db import (
        SessionLocal,
        init_db,
    )
except ImportError as e:
    logger.error(
        "Failed to import necessary modules. "
        "Ensure paths and installations are correct: %s",
        e,
    )
    logger.error("Make sure you run this script from the project root directory.")
    # Raise instead of exit if called as a module
    raise


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        logger.exception("Database transaction failed. Rolling back.")
        db.rollback()
        raise
    finally:
        db.close()


def load_users_from_json(file_path: Path) -> set[str]:
    """Load unique usernames from a JSON file."""
    if not file_path.exists():
        logger.warning("JSON file not found: %s", file_path)
        return set()
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {str(user).lower() for user in data if isinstance(user, str)}
            logger.warning("JSON file does not contain a list: %s", file_path)
            return set()
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Error reading or parsing JSON file %s: %s", file_path, e)
        return set()


def import_users_from_json() -> None:  # Renamed for clarity
    """Import users from target JSON files into the database.
    Checks for existing users and updates privacy status if different.
    """
    logger.info("Starting user import from JSON...")
    target_dir = RESOURCES_DIRECTORY / "target"
    public_users_path = target_dir / "public_users.json"
    private_users_path = target_dir / "private_users.json"

    public_users = load_users_from_json(public_users_path)
    private_users = load_users_from_json(private_users_path)

    all_users: dict[str, bool] = {}
    for user in public_users:
        all_users[user] = False
    for user in private_users:
        all_users[user] = True

    if not all_users:
        logger.info("No users found in JSON files to import.")
        return

    logger.info(
        "Found %d unique users in JSON files. Syncing with database...", len(all_users)
    )

    added_count = 0
    skipped_count = 0
    updated_count = 0

    try:
        logger.debug("Ensuring database tables exist...")
        init_db()

        with get_session() as db:
            # Fetch existing profiles (username and privacy status) for checking
            results = db.execute(select(DbProfile.username, DbProfile.is_private)).all()
            existing_profiles_map: dict[str, bool] = {row[0]: row[1] for row in results}
            logger.info(
                "Found %d existing users in the database.", len(existing_profiles_map)
            )

            for username, is_private in all_users.items():
                username_lower = username.lower()
                if username_lower in existing_profiles_map:
                    # User exists, check if privacy status needs update
                    current_privacy = existing_profiles_map[username_lower]
                    if current_privacy != is_private:
                        try:
                            profile_to_update = db.scalars(
                                select(DbProfile).where(
                                    DbProfile.username == username_lower
                                )
                            ).one()
                            profile_to_update.is_private = is_private
                            updated_count += 1
                            logger.debug(
                                "Updating privacy for existing user '%s' to %s",
                                username_lower,
                                is_private,
                            )
                        except Exception:
                            logger.exception(
                                "Failed to update profile '%s'", username_lower
                            )
                    else:
                        skipped_count += 1
                else:
                    logger.debug(
                        "Adding new user: %s (Private: %s)", username_lower, is_private
                    )
                    new_profile = DbProfile(
                        username=username_lower, is_private=is_private
                    )
                    db.add(new_profile)
                    added_count += 1

            # Commit happens automatically via context manager

    except Exception:
        logger.error("User import process failed.")
        raise

    logger.debug("User import finished.")
    logger.debug("Users Added: %d", added_count)
    logger.debug("Users Skipped (exists, no change): %d", skipped_count)
    logger.debug("Users Updated (privacy status): %d", updated_count)


# Keep the __main__ block for standalone execution if needed
if __name__ == "__main__":
    logger.info("Starting user import script standalone...")
    try:
        import_users_from_json()
        logger.info("User import script finished successfully.")
    except Exception as e:
        logger.error("Standalone user import failed: %s", e)
