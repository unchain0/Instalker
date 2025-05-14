import json
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.settings import RESOURCES_DIRECTORY
from src.core.db import Profile as DbProfile
from src.core.db import (
    SessionLocal,
    init_db,
)
from src.utils.logger import setup_logging


class UserImporter:
    """
    Imports users from JSON files into the database, checking for existing
    users and updating their privacy status if different.
    """

    def __init__(self) -> None:
        self.logger = setup_logging()

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """Provide a transactional scope around a series of operations."""
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            self.logger.exception("Database transaction failed. Rolling back.")
            db.rollback()
            raise
        finally:
            db.close()

    def _load_users_from_json(self, file_path: Path) -> set[str]:
        """Load unique usernames from a JSON file."""
        if not file_path.exists():
            self.logger.warning("JSON file not found: %s", file_path)
            return set()
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {str(user).lower() for user in data if isinstance(user, str)}
                self.logger.warning("JSON file does not contain a list: %s", file_path)
                return set()
        except (json.JSONDecodeError, OSError):
            self.logger.exception("Error reading or parsing JSON file %s", file_path)
            return set()

    @staticmethod
    def _build_user_map(public_users: Iterable[str], private_users: Iterable[str]) -> dict[str, bool]:
        """Builds a map of users with their privacy status."""
        all_users: dict[str, bool] = {}
        for user in public_users:
            all_users[user] = False  # False means public
        for user in private_users:
            all_users[user] = True  # True means private
        return all_users

    @staticmethod
    def _get_existing_profiles(db: Session) -> dict[str, bool]:
        """Fetches existing user profiles from the database."""
        results = db.execute(select(DbProfile.username, DbProfile.is_private)).all()
        return {str(row[0]).lower(): bool(row[1]) for row in results}

    def _update_user_privacy(self, db: Session, username_lower: str, *, is_private: bool) -> None:
        """Updates the privacy of an existing user."""
        profile_to_update = db.scalars(select(DbProfile).where(DbProfile.username == username_lower)).one()
        profile_to_update.is_private = is_private
        self.logger.debug(
            "Updating privacy for existing user '%s' to %s",
            username_lower,
            "Private" if is_private else "Public",
        )

    def _add_new_user(self, db: Session, username_lower: str, *, is_private: bool) -> None:
        """Adds a new user to the database."""
        self.logger.debug(
            "Adding new user: %s (Private: %s)",
            username_lower,
            "Private" if is_private else "Public",
        )
        new_profile = DbProfile(username=username_lower, is_private=is_private)
        db.add(new_profile)

    def _process_users(
        self,
        all_users: dict[str, bool],
        existing_profiles_map: dict[str, bool],
        db: Session,
    ) -> tuple[int, int, int]:
        """Processes the users, adding new users and updating existing ones."""
        added_count, skipped_count, updated_count = 0, 0, 0
        for username, is_private_from_json in all_users.items():
            username_lower = username.lower()
            if username_lower in existing_profiles_map:
                current_db_privacy = existing_profiles_map[username_lower]
                if current_db_privacy != is_private_from_json:
                    try:
                        self._update_user_privacy(db, username_lower, is_private=is_private_from_json)
                        updated_count += 1
                    except Exception:
                        self.logger.exception("Failed to update profile '%s'", username_lower)
                else:
                    skipped_count += 1
            else:
                self._add_new_user(db, username_lower, is_private=is_private_from_json)
                added_count += 1
        return added_count, skipped_count, updated_count

    def _log_summary(self, added_count: int, skipped_count: int, updated_count: int) -> None:
        """Logs the final summary of the import process."""
        self.logger.info("User import finished.")
        self.logger.info("Users Added: %d", added_count)
        self.logger.info("Users Skipped (exists, no change): %d", skipped_count)
        self.logger.info("Users Updated (privacy status): %d", updated_count)

    def execute_import(self) -> None:
        """
        Main method to import users from target JSON files into the database.
        """
        self.logger.info("Starting user import from JSON...")
        target_dir = RESOURCES_DIRECTORY / "target"
        public_users_path = target_dir / "public_users.json"
        private_users_path = target_dir / "private_users.json"

        public_users = self._load_users_from_json(public_users_path)
        private_users = self._load_users_from_json(private_users_path)

        all_users_map: dict[str, bool] = self._build_user_map(public_users, private_users)

        if not all_users_map:
            self.logger.info("No users found in JSON files to import.")
            return

        self.logger.info(
            "Found %d unique users in JSON files. Syncing with database...",
            len(all_users_map),
        )

        added_count, skipped_count, updated_count = 0, 0, 0

        try:
            self.logger.debug("Ensuring database tables exist...")
            init_db()  # Ensure tables are created

            with self._get_session() as db:
                existing_profiles_map = self._get_existing_profiles(db)
                added_count, skipped_count, updated_count = self._process_users(
                    all_users_map, existing_profiles_map, db
                )
        except Exception:
            self.logger.exception("User import process failed.")
        finally:
            self._log_summary(added_count, skipped_count, updated_count)
