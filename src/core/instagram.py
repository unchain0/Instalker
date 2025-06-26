import contextlib
import os
import sys
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from platform import system
from sqlite3 import Connection, OperationalError, connect
from typing import Any, cast

from instaloader import (
    ConnectionException,
    Instaloader,
    InstaloaderException,
    LatestStamps,
    Profile,
    ProfileNotExistsException,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from tqdm import tqdm

from src.core.db import Hashtag, Mention
from src.core.db import Profile as DbProfile
from src.utils import (
    DOWNLOAD_DIRECTORY,
    LATEST_STAMPS,
    setup_logging,
)


class Instagram:
    """Manages Instagram downloads and session handling.

    Handles fetching profiles, downloading content,
    and managing login sessions via Firefox cookies.
    """

    @staticmethod
    @contextlib.contextmanager
    def _suppress_output() -> Generator[None, Any]:
        """Context manager to suppress stdout and stderr output.

        Uses Path.open() with explicit encoding for better compatibility.
        """
        with (
            Path(os.devnull).open("w", encoding="utf-8") as devnull,
            contextlib.redirect_stdout(devnull),
            contextlib.redirect_stderr(devnull),
        ):
            yield

    def __init__(
        self,
        db: Session,
        users: set[str] | None = None,
        *,
        highlights: bool = False,
    ) -> None:
        """Initialize the class with settings, configurations, and DB session.

        :param db: The SQLAlchemy database session.
        :type db: Session
        :param users: Optional explicit set of usernames to target, overriding JSON file.
        :type users: Optional[set[str]]
        :param highlights: Whether to download highlights or not.
        :type highlights: bool
        """
        self.logger = setup_logging()
        self.db = db

        self.logger.info("Starting main Instagram processing...")

        if users is not None:
            self.users = users
            self.logger.info("Using explicitly provided list of %d users.", len(self.users))
        else:
            # Fetch users from the database
            db_profiles = self.db.query(DbProfile).all()
            self.users = {profile.username for profile in db_profiles}
            self.logger.info(
                "Fetched %d users from the database.",
                len(self.users),
            )

        self.highlights = highlights
        self.latest_stamps = LatestStamps(LATEST_STAMPS)  # type: ignore[no-untyped-call]

        if not (cookie_file := self._get_cookie_file()):
            err = "No Firefox cookies.sqlite file found."
            raise SystemExit(err)

        self.conn: Connection = connect(f"file:{cookie_file}?immutable=1", uri=True)

        self.loader = Instaloader(
            quiet=True,
            filename_pattern="{profile}_{date_utc}_UTC",
            title_pattern="{profile}_{date_utc}_UTC",
            save_metadata=False,
            post_metadata_txt_pattern="",
            fatal_status_codes=[400, 429],
        )

    def run(self) -> None:
        """Execute the main sequence of operations for the class."""
        self._import_session()
        self._download()

        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            self.logger.debug("Closed connection to cookie database.")

    def _download(self) -> None:
        """Download Instagram profiles and their content, updating the database."""
        self.logger.info("Starting download process for %d users", len(self.users))

        progress_bar = tqdm(sorted(self.users), desc="Downloading profiles", unit="profile", leave=True)

        for user in progress_bar:
            progress_bar.set_postfix(user=user)

            try:
                profile = self._get_instagram_profile(user)
                if not profile:
                    continue

                db_profile = self._upsert_profile_to_db(profile)
                if not db_profile:
                    self.logger.error("Failed to save profile '%s' to database.", user)
                    continue

                self.loader.dirname_pattern = str(DOWNLOAD_DIRECTORY / user)

                if db_profile.is_private and not profile.followed_by_viewer:
                    continue

                with Instagram._suppress_output():
                    self._download_profile_content(profile)
            except (
                ProfileNotExistsException,
                ConnectionException,
                KeyError,
                PermissionError,
            ):
                self.logger.exception("Error processing user '%s'", user)
            finally:
                pass

    def _get_or_create_item(self, item_text: str, model_class: type, field_name: str) -> Any:
        stmt = select(model_class).where(item_text == getattr(model_class, field_name))
        item = self.db.scalars(stmt).one_or_none()
        if not item:
            item = model_class(**{field_name: item_text})
            self.db.add(item)
        return item

    def _upsert_profile_to_db(self, profile: Profile) -> DbProfile | None:
        """Creates or updates a profile record in the database."""
        username = profile.username
        self.logger.debug("Upserting profile '%s' to database.", username)

        try:
            stmt = select(DbProfile).where(DbProfile.username == username)
            db_profile = self.db.scalars(stmt).one_or_none()

            profile_data = {
                "full_name": profile.full_name,
                "biography": profile.biography,
                "followers": profile.followers,
                "followees": profile.followees,
                "post_count": profile.mediacount,
                "business_category_name": profile.business_category_name,
                "external_url": profile.external_url,
                "is_private": profile.is_private,
                "blocked_by_viewer": profile.blocked_by_viewer,
                "followed_by_viewer": profile.followed_by_viewer,
                "follows_viewer": profile.follows_viewer,
                "last_checked": datetime.now(UTC),
            }

            hashtags = []
            if profile.biography_hashtags:
                for tag_text in profile.biography_hashtags:
                    hashtag = self._get_or_create_item(tag_text, Hashtag, "tag")
                    hashtags.append(hashtag)

            mentions = []
            if profile.biography_mentions:
                for mention_username in profile.biography_mentions:
                    mention = self._get_or_create_item(mention_username, Mention, "username")
                    mentions.append(mention)

            if db_profile:
                self.logger.debug("Updating existing DB profile for '%s'.", username)
                for key, value in profile_data.items():
                    setattr(db_profile, key, value)
                db_profile.hashtags = hashtags
                db_profile.mentions = mentions
            else:
                self.logger.debug("Creating new DB profile for '%s'.", username)
                db_profile = DbProfile(username=username, **profile_data)
                db_profile.hashtags = hashtags
                db_profile.mentions = mentions
                self.db.add(db_profile)

            self.logger.debug("Committed changes for profile '%s'.", username)

        except SQLAlchemyError:
            self.logger.exception(
                "Database error upserting profile '%s'",
                username,
            )
            self.db.rollback()
            return None
        else:
            return db_profile

    def _download_profile_content(self, profile: Profile) -> None:
        """Download profile content including posts, stories, and highlights.

        :param profile: Instagram profile to download.
        :type profile: Profile
        """
        self.logger.debug("Downloading content for profile '%s'.", profile.username)
        try:
            self.loader.download_profiles(
                {profile},
                tagged=False,
                stories=True,
                reels=True,
                latest_stamps=self.latest_stamps,
            )
            if self.highlights:
                self._download_profile_highlights(profile)
        except (KeyError, PermissionError):
            self.logger.exception("Error downloading content for profile '%s'", profile.username)

    def _download_profile_highlights(self, profile: Profile) -> None:
        """Download profile highlights if enabled.

        :param profile: Instagram profile to download highlights from.
        :type profile: Profile
        """
        self.logger.debug("Downloading highlights for profile '%s'.", profile.username)
        try:
            self.loader.download_highlights(profile, fast_update=True, filename_target=None)
        except (KeyError, ConnectionException, AssertionError):
            self.logger.exception(
                "Error downloading highlights for profile '%s'",
                profile.username,
            )

    def _fetch_and_load_cookies(self) -> dict[str, str] | None:
        """Fetch Instagram cookies from Firefox and load them into Instaloader.

        :raises OperationalError: If there's an error, read the cookie database.
        :return: A dictionary of cookies if found, otherwise None.
        :rtype: dict[str, str] | None
        """
        self.logger.debug("Fetching Instagram cookies from Firefox.")
        try:
            cookie_data = self.conn.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'")
            cookies = dict(cookie_data.fetchall())
            if not cookies:
                self.logger.warning("No Instagram cookies found in the Firefox cookie database.")
                return None

            self.loader.context.update_cookies(cookies)  # type: ignore[no-untyped-call]
        except OperationalError:
            self.logger.exception("Error reading Firefox cookie database")
        else:
            return cookies
        return None

    def _test_login_status(self) -> None:
        """Test the Instaloader login status. Assumes cookies have been loaded.

        :raises SystemExit: If login fails or for other Instaloader errors.
        """
        self.logger.debug("Testing Instaloader login status.")
        try:
            if not (username := self.loader.test_login()):
                self.logger.error("Failed to log in using imported cookies.")
                sys.exit()

            self.logger.info("Session valid for '%s'", username)
            self.loader.context.username = username  # type: ignore[assignment]
        except InstaloaderException:
            self.logger.exception("Instaloader error during login test")

    def _import_session(self) -> None:
        """Import session from Firefox cookies and verify login.

        :raises SystemExit: If cookie DB error, no cookies are found, or login fails.
        """
        self.logger.debug("Attempting to import session cookie from Firefox.")
        try:
            cookies = self._fetch_and_load_cookies()  # Can raise SystemExit for DB error
            if not cookies:
                sys.exit("No Instagram cookies found in Firefox. Cannot proceed.")

            self._test_login_status()
        except (OperationalError, InstaloaderException, ConnectionException):
            self.logger.exception("Error during session import.")
            sys.exit("Failed to import session.")

    def _get_instagram_profile(self, username: str) -> Profile | None:
        """Retrieve the Instaloader profile object for a given user.

        :param username: The Instagram username to retrieve the profile from.
        :type username: str
        :return: The Instaloader Profile object if found, otherwise None.
        :rtype: Profile | None
        """
        self.logger.debug("Attempting to fetch Instaloader profile for '%s'.", username)
        try:
            profile = Profile.from_username(self.loader.context, username)
            if not hasattr(profile, "userid"):
                self.logger.warning("Fetched profile for '%s' seems incomplete.", username)
                return None
            self.logger.debug("Successfully fetched Instaloader profile for '%s'.", username)
            return cast("Profile", profile)
        except ProfileNotExistsException:
            self.logger.info("Profile '%s' does not exist.", username)
        except ConnectionException:
            self.logger.exception("Connection error retrieving profile '%s'", username)
        except InstaloaderException:
            self.logger.exception("Instaloader error retrieving profile '%s'", username)
        except (AttributeError, TypeError, ValueError):
            self.logger.exception("Unexpected error retrieving profile '%s'.", username)
        return None

    def _get_cookie_file(self) -> str | None:
        """Retrieve the path to the Firefox cookies file based on the system.

        :return: The path to the Firefox cookies file or None if not found.
        :rtype: str | None
        """
        default_patterns = {
            "Windows": "AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
            "Darwin": "Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
            "Linux": ".mozilla/firefox/*/cookies.sqlite",
        }

        pattern = default_patterns.get(system(), ".mozilla/firefox/*/cookies.sqlite")
        try:
            cookie_paths = list(Path.home().glob(pattern))
            if cookie_paths:
                return str(cookie_paths[0])
        except (PermissionError, OSError):
            self.logger.exception("Error accessing cookie file")
        return None
