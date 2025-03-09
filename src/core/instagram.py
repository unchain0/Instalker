"""Provides functionality to manage Instagram profile downloads and session handling.

This module includes classes and methods to handle downloading Instagram profiles,
managing sessions, and importing session cookies from Firefox.
"""

import logging
from glob import glob
from os.path import expanduser
from platform import system
from sqlite3 import OperationalError, connect

from instaloader import Instaloader, LatestStamps, Profile, ProfileNotExistsException
from tqdm import tqdm

from src import DOWNLOAD_DIRECTORY, LATEST_STAMPS, TARGET_USERS


class Instagram:
    """A class to manage Instagram profile downloads and session handling."""

    def __init__(
        self,
        users: set[str] | None = None,
        *,
        highlights: bool = False,
    ) -> None:
        """Initialize the Instagram class with default settings and configurations.

        Args:
            users (set[str]): The set of Instagram usernames to download content from.
            highlights (bool): Whether to download highlights or not.

        """
        self.download_directory = DOWNLOAD_DIRECTORY
        self.users = users if users is not None else TARGET_USERS
        self.highlights = highlights
        self.latest_stamps = LatestStamps(LATEST_STAMPS)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.loader = Instaloader(
            filename_pattern="{target}_{date_utc}_UTC",
            title_pattern="{target}_{date_utc}_UTC",
            quiet=True,
            save_metadata=False,
            post_metadata_txt_pattern="",
            fatal_status_codes=[400],
        )

    def run(self) -> None:
        """Execute the main sequence of operations for the class."""
        self._import_session()
        self._download()

    def _download(self) -> None:
        """Download Instagram profiles and their content."""
        self.logger.info("Starting download process for %d users", len(self.users))
        progress_bar = tqdm(
            self.users,
            desc="Downloading profiles",
            unit="profile",
        )
        for user in progress_bar:
            progress_bar.set_postfix(
                user=user,
            )

            profile = self._get_instagram_profile(user)
            if not profile:
                continue

            self.loader.dirname_pattern = str(DOWNLOAD_DIRECTORY / user)

            if profile.is_private and not profile.followed_by_viewer:
                self.loader.download_profilepic_if_new(profile, self.latest_stamps)
                continue

            try:
                self.loader.download_profiles(
                    {profile},
                    tagged=False,  # Unstable feature
                    stories=True,
                    reels=True,
                    latest_stamps=self.latest_stamps,
                )
            except KeyError:
                self.logger.exception(
                    "Error downloading profile '%s'",
                    profile.username,
                )

            if self.highlights:
                try:
                    self.loader.download_highlights(profile, fast_update=True)
                except KeyError:
                    self.logger.exception(
                        "Error downloading highlights for profile '%s'",
                        profile.username,
                    )

        self.logger.info("Download completed.")

    def _import_session(self) -> None:
        """Import the session cookies from Firefox's cookies.sqlite for Instagram."""
        cookie_file = self._get_cookie_file()
        if not cookie_file:
            err = "No Firefox cookies.sqlite file found."
            raise SystemExit(err)

        conn = connect(f"file:{cookie_file}?immutable=1", uri=True)
        try:
            cookie_data = conn.execute(
                "SELECT name, value FROM moz_cookies WHERE baseDomain='instagram.com'",
            )
        except OperationalError:
            cookie_data = conn.execute(
                "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'",
            )
        self.loader.context._session.cookies.update(  # type: ignore[reportPrivateUsage]
            dict(cookie_data),
        )
        username = self.loader.test_login()
        if not username:
            err = "Not logged in. Are you logged in successfully in Firefox?"
            raise SystemExit(err)

        self.logger.info("Imported session cookie for '%s'", username)
        self.loader.context.username = username

    def _get_instagram_profile(self, username: str) -> Profile | None:
        """Retrieve the Instagram profile of a given user.

        Args:
            username (str): The Instagram username to retrieve the profile from.

        Returns:
            Profile | None: The Instagram profile of the user, if found.

        """
        try:
            profile = Profile.from_username(self.loader.context, username)
            self.logger.debug(
                "Username: '%s', Followers: %d, Posts: %d, Private: '%s'",
                username,
                profile.followers,
                profile.mediacount,
                profile.is_private,
            )
        except ProfileNotExistsException:
            self.logger.info("Profile '%s' not found", username)
            return None
        except Exception:
            self.logger.exception("Error retrieving profile '%s'", username)
            return None
        else:
            return profile

    @staticmethod
    def _get_cookie_file() -> str | None:
        """Retrieve the path to the Firefox cookies.sqlite file based on the system.

        Returns:
            str: The path to the Firefox cookies.sqlite file.

        """
        default_cookie_file = {
            "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
            "Darwin": "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
        }.get(system(), "~/.mozilla/firefox/*/cookies.sqlite")
        cookie_files = glob(expanduser(default_cookie_file))
        if not cookie_files:
            err = "No Firefox cookies.sqlite file found."
            raise SystemExit(err)
        return cookie_files[0]
