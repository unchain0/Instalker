"""Provides functionality to manage Instagram downloads and session handling.

Module includes classes and methods to handle downloading Instagram profiles,
managing sessions, and importing session cookies from Firefox.
"""

import json
import logging
from contextlib import contextmanager
from pathlib import Path
from platform import system
from sqlite3 import Connection, OperationalError, connect
from typing import Iterator, List, Optional, Set

from instaloader import (
    ConnectionException,
    Instaloader,
    InstaloaderException,
    LatestStamps,
    Profile,
    ProfileNotExistsException,
)
from tqdm import tqdm

from src.config.settings import (
    DOWNLOAD_DIRECTORY,
    LATEST_STAMPS,
    RESOURCES_DIRECTORY,
    TARGET_USERS,
)


class Instagram:
    """A class to manage Instagram profile downloads and session handling."""

    def __init__(
        self,
        users: Optional[Set[str]] = None,
        *,
        highlights: bool = False,
    ) -> None:
        """Initialize the class with default settings and configurations.

        Args:
            users: The set of usernames to download content from
            highlights: Whether to download highlights or not
        """
        self.download_directory = DOWNLOAD_DIRECTORY
        self.users = users if users is not None else TARGET_USERS
        self.highlights = highlights
        self.latest_stamps = LatestStamps(LATEST_STAMPS)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.loader = Instaloader(
            filename_pattern="{profile}_{date_utc}_UTC",
            title_pattern="{profile}_{date_utc}_UTC",
            quiet=True,
            save_metadata=False,
            post_metadata_txt_pattern="",
            fatal_status_codes=[400, 429],
        )

        self.public_users = self._load_user_list("public_users.json")
        self.private_users = self._load_user_list("private_users.json")
        self.logger.info(
            "Loaded %d public users and %d private users from existing files",
            len(self.public_users),
            len(self.private_users),
        )

    def run(self) -> None:
        """Execute the main sequence of operations for the class."""
        if not self.users:
            self.logger.warning(
                "No target users specified. Please add users to the configuration.",
            )
            return

        try:
            self._import_session()
            self._download()
            self._save_user_lists()
        except Exception as e:
            self.logger.exception("Fatal error in Instagram processing: %s", e)
            raise

    def _download(self) -> None:
        """Download Instagram profiles and their content."""
        self.logger.info("Starting download process for %d users", len(self.users))
        progress_bar = tqdm(
            sorted(self.users),
            desc="Downloading profiles",
            unit="profile",
        )

        for user in progress_bar:
            progress_bar.set_postfix(user=user)

            try:
                profile = self._get_instagram_profile(user)
                if not profile:
                    continue

                self._update_user_privacy_status(user, profile)
                self.loader.dirname_pattern = str(DOWNLOAD_DIRECTORY / user)

                if profile.is_private and not profile.followed_by_viewer:
                    self.loader.download_profilepic_if_new(profile, self.latest_stamps)
                    continue

                self._download_profile_content(profile)
            except (
                ProfileNotExistsException,
                ConnectionException,
                KeyError,
                PermissionError,
            ) as e:
                self.logger.error("Error processing user '%s': %s", user, e)

        self.logger.info("Download process completed for all users.")

    def _update_user_privacy_status(self, user: str, profile: Profile) -> None:
        """Update user's privacy status in our tracking lists.

        Args:
            user: Instagram username
            profile: Instagram profile object
        """
        was_public = user in self.public_users
        was_private = user in self.private_users
        is_private = profile.is_private

        if is_private and was_public:
            self.logger.info("User '%s' changed from public to private", user)
            self.public_users.remove(user)
        elif not is_private and was_private:
            self.logger.info("User '%s' changed from private to public", user)
            self.private_users.remove(user)

        if is_private and not was_private:
            self.private_users.append(user)
        elif not is_private and not was_public:
            self.public_users.append(user)

    def _download_profile_content(self, profile: Profile) -> None:
        """Download profile content including posts, stories, and highlights.

        Args:
            profile: Instagram profile to download
        """
        try:
            self.loader.download_profiles(
                {profile},
                tagged=False,  # Unstable feature
                stories=True,
                reels=True,
                latest_stamps=self.latest_stamps,
            )
            if self.highlights:
                self._download_profile_highlights(profile)
        except (KeyError, PermissionError) as e:
            self.logger.error(
                "Error downloading profile '%s': %s",
                profile.username,
                e,
            )

    def _download_profile_highlights(self, profile: Profile) -> None:
        """Download profile highlights if enabled.

        Args:
            profile: Instagram profile to download highlights from
        """
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

    def _load_user_list(self, filename: str) -> List[str]:
        """Load user list from JSON file.

        Args:
            filename: Name of the JSON file to load

        Returns:
            List of usernames from the file or empty list if file doesn't exist
        """
        file_path = RESOURCES_DIRECTORY / "target" / filename
        if not file_path.exists():
            return []

        try:
            with Path.open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as e:
            self.logger.warning("Error loading %s: %s", filename, e)
            return []

    def _save_user_lists(self) -> None:
        """Save the public and private user lists to JSON files."""
        target_dir = RESOURCES_DIRECTORY / "target"
        target_dir.mkdir(parents=True, exist_ok=True)

        private_path = target_dir / "private_users.json"
        with Path.open(private_path, "w", encoding="utf-8") as file:
            json.dump(sorted(self.private_users), file, indent=4)

        public_path = target_dir / "public_users.json"
        with Path.open(public_path, "w", encoding="utf-8") as file:
            json.dump(sorted(self.public_users), file, indent=4)

        self.logger.info(
            "Saved %d private users to %s and %d public users to %s",
            len(self.private_users),
            private_path.name,
            len(self.public_users),
            public_path.name,
        )

    def _import_session(self) -> None:
        """Import the session cookies from Firefox's cookies for Instagram.

        Raises:
            SystemExit: If no cookie file is found or login fails
        """
        cookie_file = self._get_cookie_file()
        if not cookie_file:
            err = "No Firefox cookies.sqlite file found."
            raise SystemExit(err)

        with self._open_cookie_db(cookie_file) as conn:
            try:
                cookie_data = conn.execute(
                    "SELECT name, value "
                    + "FROM moz_cookies "
                    + "WHERE baseDomain='instagram.com'"
                )
            except OperationalError:
                cookie_data = conn.execute(
                    "SELECT name, value "
                    + "FROM moz_cookies "
                    + "WHERE host LIKE '%instagram.com'"
                )
            self.loader.context.update_cookies(dict(cookie_data))  # type: ignore[reportUnknownMemberType]

        username = self.loader.test_login()
        if not username:
            err = "Not logged in. Are you logged in successfully in Firefox?"
            raise SystemExit(err)

        self.logger.info("Imported session cookie for '%s'", username)
        self.loader.context.username = username

    @contextmanager
    def _open_cookie_db(self, cookie_file: str) -> Iterator[Connection]:
        """Open the Firefox cookie database with proper handling.

        Args:
            cookie_file: Path to Firefox cookies.sqlite file

        Yields:
            SQLite connection to the cookie database
        """
        conn = connect(f"file:{cookie_file}?immutable=1", uri=True)
        try:
            yield conn
        finally:
            conn.close()

    def _get_instagram_profile(self, username: str) -> Optional[Profile]:
        """Retrieve the Instagram profile of a given user.

        Args:
            username: The Instagram username to retrieve the profile from

        Returns:
            The Instagram profile of the user, if found
        """
        try:
            profile = Profile.from_username(self.loader.context, username)
            self.logger.debug(
                "Username: '%s', Followers: %d, Posts: %d, Private: %s",
                username,
                profile.followers,
                profile.mediacount,
                "Yes" if profile.is_private else "No",
            )
            return profile
        except ProfileNotExistsException:
            self.logger.info("Profile '%s' not found", username)
        except ConnectionException as e:
            self.logger.error(
                "Connection error retrieving profile '%s': %s", username, e
            )
        except InstaloaderException as e:
            self.logger.exception(
                "Instaloader error retrieving profile '%s': %s", username, e
            )

    @staticmethod
    def _get_cookie_file() -> Optional[str]:
        """Retrieve the path to the Firefox cookies file based on the system.

        Returns:
            The path to the Firefox cookies file or None if not found
        """
        default_patterns = {
            "Windows": "AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
            "Darwin": "Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
            "Linux": ".mozilla/firefox/*/cookies.sqlite",
        }

        pattern = default_patterns.get(system(), ".mozilla/firefox/*/cookies.sqlite")

        cookie_paths = list(Path.home().glob(pattern))

        return str(cookie_paths[0]) if cookie_paths else None
