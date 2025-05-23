"""Provides functionality to manage Instagram downloads and session handling.

Module includes classes and methods to handle downloading Instagram profiles,
managing sessions, and importing session cookies from Firefox.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from platform import system
from sqlite3 import Connection, OperationalError, connect
from typing import Literal, cast

from instaloader import (
    ConnectionException,
    Instaloader,
    InstaloaderException,
    LatestStamps,
    Profile,
    ProfileNotExistsException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from tqdm import tqdm

from src.config.settings import (
    DOWNLOAD_DIRECTORY,
    LATEST_STAMPS,
)
from src.core.db import Hashtag, Mention
from src.core.db import Profile as DbProfile


class Instagram:
    """Manages Instagram downloads and session handling, integrated with DB.

    Handles fetching profiles, updating database records, downloading content,
    and managing login sessions via Firefox cookies.
    """

    def __init__(
        self,
        db: Session,
        users: set[str] | None = None,
        *,
        highlights: bool = False,
        target_users: Literal["all", "public", "private"] = "all",
    ) -> None:
        """Initialize the class with settings, configurations, and DB session.

        :param db: The SQLAlchemy database session.
        :type db: Session
        :param users: Optional explicit set of usernames to target, overriding DB query.
        :type users: Optional[set[str]]
        :param highlights: Whether to download highlights or not.
        :type highlights: bool
        :param target_users: Filter users from DB ('all', 'public', 'private').
        :type target_users: Literal["all", "public", "private"]
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db

        if users is not None:
            self.users = users
            self.logger.info(
                "Using explicitly provided list of %d users.", len(self.users)
            )
        else:
            self.users = self._get_users_from_db(target_users)
            self.logger.info(
                "Fetched %d users from database based on target '%s'.",
                len(self.users),
                target_users,
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

    def _get_users_from_db(
        self, target: Literal["all", "public", "private"]
    ) -> set[str]:
        """Fetches usernames from the database based on privacy status."""
        stmt = select(DbProfile.username)
        if target == "public":
            stmt = stmt.where(DbProfile.is_private.is_(False))
        elif target == "private":
            stmt = stmt.where(DbProfile.is_private.is_(True))

        return set(self.db.scalars(stmt).all())

    def run(self) -> None:
        """Execute the main sequence of operations for the class."""
        if not self.users:
            self.logger.warning(
                "No target users specified or found in DB for filter. "
                "Please add users to the database.",
            )
            return

        self._import_session()
        self._download()

        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            self.logger.debug("Closed connection to cookie database.")

    def _download(self) -> None:
        """Download Instagram profiles and their content, updating the database."""
        self.logger.info("Starting download process for %d users", len(self.users))

        progress_bar = tqdm(
            sorted(self.users), desc="Downloading profiles", unit="profile", leave=True
        )

        for user in progress_bar:
            progress_bar.set_postfix(user=user)
            profile: Profile | None = None
            db_profile: DbProfile | None = None

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

                self._download_profile_content(profile)
            except (
                ProfileNotExistsException,
                ConnectionException,
                KeyError,
                PermissionError,
            ) as e:
                self.logger.error(
                    "Error processing user '%s': %s", user, e, exc_info=True
                )
            finally:
                pass

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
                    tag_stmt = select(Hashtag).where(Hashtag.tag == tag_text)
                    hashtag = self.db.scalars(tag_stmt).one_or_none()
                    if not hashtag:
                        hashtag = Hashtag(tag=tag_text)
                        self.db.add(hashtag)
                    hashtags.append(hashtag)

            mentions = []
            if profile.biography_mentions:
                for mention_username in profile.biography_mentions:
                    mention_stmt = select(Mention).where(
                        Mention.username == mention_username
                    )
                    mention = self.db.scalars(mention_stmt).one_or_none()
                    if not mention:
                        mention = Mention(username=mention_username)
                        self.db.add(mention)
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

            self.db.commit()
            self.logger.debug("Committed changes for profile '%s'.", username)
            return db_profile

        except Exception as e:
            self.logger.error(
                "Database error upserting profile '%s': %s", username, e, exc_info=True
            )
            self.db.rollback()
            return None

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
        except (KeyError, PermissionError) as e:
            self.logger.error(
                "Error downloading content for profile '%s': %s",
                profile.username,
                e,
            )

    def _download_profile_highlights(self, profile: Profile) -> None:
        """Download profile highlights if enabled.

        :param profile: Instagram profile to download highlights from.
        :type profile: Profile
        """
        self.logger.debug("Downloading highlights for profile '%s'.", profile.username)
        try:
            self.loader.download_highlights(
                profile, fast_update=True, filename_target=None
            )
        except (KeyError, ConnectionException, AssertionError) as e:
            self.logger.error(
                "Error downloading highlights for profile '%s': %s",
                profile.username,
                e,
            )

    def _import_session(self) -> None:
        """Import the session cookies from Firefox's cookies for Instagram.

        :raises SystemExit: If no cookie file is found or login fails.
        """
        self.logger.debug("Attempting to import session cookie from Firefox.")
        try:
            cookie_data = self.conn.execute(
                "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'"
            )
            cookies = dict(cookie_data.fetchall())
            if not cookies:
                self.logger.warning(
                    "No Instagram cookies found in the Firefox cookie database."
                )
                raise SystemExit(
                    "No Instagram cookies found in the Firefox cookie database."
                )

            if cookies:
                self.loader.context.update_cookies(cookies)  # type: ignore[no-untyped-call]
                self.logger.debug(
                    "Loaded %d Instagram cookies into context.", len(cookies)
                )

            if not (username := self.loader.test_login()):
                if not cookies:
                    self.logger.warning(
                        "Proceeding without authentication (no cookies found)."
                    )
                else:
                    self.logger.error("Failed to log in using imported cookies.")
                    raise SystemExit("Login failed. Are Firefox cookies up-to-date?")
            self.logger.info(
                "Successfully logged in or session valid for '%s'", username
            )
            self.loader.context.username = username  # type: ignore[assignment]

        except OperationalError as e:
            self.logger.error("Error reading Firefox cookie database: %s", e)
            raise SystemExit(f"Error accessing cookie DB: {e}") from e
        except InstaloaderException as e:
            self.logger.error(
                "Instaloader error during session import/login test: %s", e
            )
            raise SystemExit(f"Instaloader login/session error: {e}") from e
        except Exception as e:
            self.logger.exception("Unexpected error during session import.")
            raise SystemExit(f"Unexpected error during session import: {e}") from e

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
                self.logger.warning(
                    "Fetched profile for '%s' seems incomplete.", username
                )
                return None
            self.logger.debug(
                "Successfully fetched Instaloader profile for '%s'.", username
            )
            return cast(Profile, profile)
        except ProfileNotExistsException:
            self.logger.info("Profile '%s' does not exist.", username)
        except ConnectionException as e:
            self.logger.error(
                "Connection error retrieving profile '%s': %s", username, e
            )
        except InstaloaderException as e:
            self.logger.error(
                "Instaloader error retrieving profile '%s': %s", username, e
            )
        except Exception:
            self.logger.exception("Unexpected error retrieving profile '%s'.", username)

        return None

    @staticmethod
    def _get_cookie_file() -> str | None:
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
        except Exception as e:
            logging.error("Error searching for cookie file: %s", e)
        return None
