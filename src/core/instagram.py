import contextlib
import logging
from glob import glob
from os.path import expanduser
from platform import system
from shutil import rmtree
from sqlite3 import OperationalError, connect

import instaloader
from instaloader import Profile, ProfileNotExistsException
from tqdm import tqdm

from src import DOWNLOAD_DIRECTORY, LATEST_STAMPS, TARGET_USERS
from src.core.rate_controller import StealthRateController


class Instagram:
    """
    A class to manage Instagram profile downloads and session handling.
    """

    def __init__(self: "Instagram", users: set[str] | None) -> None:
        """
        Initialize the Instagram class with default settings and configurations.

        Args:
            users (set[str]): The set of Instagram usernames to download content from.
        """
        self.download_directory = DOWNLOAD_DIRECTORY
        self.users = users if users is not None else TARGET_USERS
        self.latest_stamps = instaloader.LatestStamps(LATEST_STAMPS)
        self.loader = instaloader.Instaloader(
            dirname_pattern=str(self.download_directory),
            quiet=True,
            save_metadata=False,
            max_connection_attempts=1,
            fatal_status_codes=[400, 401],
            rate_controller=lambda ctx: StealthRateController(ctx),
            sanitize_paths=True,
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self: "Instagram") -> None:
        """
        Execute the main sequence of operations for the class.
        """
        self._remove_all_txt()
        self._import_session()
        self._download()

    def _download(self: "Instagram") -> None:
        """
        Download Instagram profiles and their content.
        """
        progress_bar = tqdm(
            self.users,
            desc="Downloading user profiles",
            unit="profile",
            postfix={"user": None},
        )
        for user in progress_bar:
            progress_bar.set_postfix({"user": user})
            profile = self._get_instagram_profile(user)

            if not profile:
                continue

            if profile.is_private and not profile.followed_by_viewer:
                self.loader.download_profilepic_if_new(profile, self.latest_stamps)
                continue

            self.loader.download_profiles(
                {profile},
                tagged=True,
                stories=True,
                reels=True,
                latest_stamps=self.latest_stamps,
            )
            with contextlib.suppress(Exception):
                self.loader.download_igtv(profile, latest_stamps=self.latest_stamps)

        self.logger.info("Download completed.")

    def _remove_all_txt(self: "Instagram") -> None:
        """Remove all .txt files from the download directory."""
        for txt in self.download_directory.glob("*.txt"):
            rmtree(txt) if txt.is_dir() else txt.unlink()

    def _import_session(self: "Instagram") -> None:
        """
        Import the session cookies from Firefox's cookies.sqlite file for Instagram.
        """
        cookie_file = self._get_cookie_file()
        if not cookie_file:
            raise SystemExit("No Firefox cookies.sqlite file found.")

        self.logger.info("Using cookies from %s.", cookie_file)
        conn = connect(f"file:{cookie_file}?immutable=1", uri=True)
        try:
            cookie_data = conn.execute(
                "SELECT name, value FROM moz_cookies WHERE baseDomain='instagram.com'",
            )
        except OperationalError:
            cookie_data = conn.execute(
                "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'",
            )
        self.loader.context._session.cookies.update(cookie_data)  # type: ignore[arg-type]
        username = self.loader.test_login()
        if not username:
            raise SystemExit(
                "Not logged in. Are you logged in successfully in Firefox?"
            )

        self.logger.info("Imported session cookie for '%s'.", username)
        self.loader.context.username = username  # type: ignore[assignment]

    def _get_instagram_profile(self: "Instagram", username: str) -> Profile | None:
        """
        Retrieve the Instagram profile of a given user.
        """
        try:
            profile: Profile = Profile.from_username(self.loader.context, username)
        except ProfileNotExistsException:
            self.logger.info("Profile '%s' not found.", username)
            return None
        return profile

    @staticmethod
    def _get_cookie_file() -> str | None:
        """
        Retrieve the path to the Firefox cookies.sqlite file based on the system.
        """
        default_cookie_file = {
            "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
            "Darwin": "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
        }.get(system(), "~/.mozilla/firefox/*/cookies.sqlite")
        cookie_files = glob(expanduser(default_cookie_file))
        if not cookie_files:
            raise SystemExit("No Firefox cookies.sqlite file found.")
        return cookie_files[0]
