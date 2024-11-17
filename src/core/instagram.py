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


class Instagram:
    """
    A class to manage Instagram profile downloads and session handling.

    This class provides methods to download Instagram profiles, manage session cookies,
    and handle image and text file cleanup operations.
    """

    def __init__(self: "Instagram", users: set[str] | None) -> None:
        """
        Initialize the Instagram class with default settings and configurations.

        Args:
            users (set[str], optional): A set of usernames to track.
                Defaults to an empty set.

        Attributes:
            download_directory (str): The directory where downloads will be stored.
            users (set[str]): The set of usernames to track.
            latest_stamps (dict): A dictionary containing the latest timestamps
                for tracked users.
            loader (instaloader.Instaloader): An instance of the Instaloader class
                for downloading Instagram data.
            logger (logging.Logger): A logger instance for logging class activities.
        """
        self.download_directory = DOWNLOAD_DIRECTORY
        self.users = users if users is not None else TARGET_USERS
        self.latest_stamps = instaloader.LatestStamps(LATEST_STAMPS)
        self.loader = instaloader.Instaloader(
            dirname_pattern=str(self.download_directory),
            quiet=True,
            save_metadata=False,
            fatal_status_codes=[400, 401, 429],
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self: "Instagram") -> None:
        """
        Execute the main sequence of operations for the class.

        This method performs the following steps:
        1. Removes all text files.
        2. Imports the session data.
        3. Initiates the download process.
        """
        self.remove_all_txt()
        self.import_session()
        self.download()

    def download(self: "Instagram") -> None:
        """
        Download Instagram profiles and their content.

        This method iterates over a list of users and downloads their profiles.
        It displays a progress bar to indicate the download progress. For each user,
        it fetches the Instagram profile and checks if the profile is private. If the
        profile is private, it only downloads the profile picture if it's new. If the
        profile is not private, it downloads the profile content including tagged posts
        and stories.
        """
        progress_bar = tqdm(
            self.users,
            desc="Downloading user profiles",
            unit="profile",
            postfix={"user": None},
        )
        for user in progress_bar:
            progress_bar.set_postfix({"user": user})
            profile = self.get_instagram_profile(user)

            if profile is None:
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
            with contextlib.suppress(KeyError):
                self.loader.download_highlights(profile, fast_update=True)
                self.loader.download_igtv(profile, latest_stamps=self.latest_stamps)

        self.logger.info("Download completed.")

    def remove_all_txt(self: "Instagram") -> None:
        """Remove all .txt files from the download directory."""
        for txt in self.download_directory.glob("*.txt"):
            rmtree(txt) if txt.is_dir() else txt.unlink()

    def import_session(self: "Instagram") -> None:
        """
        Import the session cookies from Firefox's cookies.sqlite file for Instagram.

        This method attempts to locate the Firefox cookies.sqlite file and extract
        cookies related to Instagram. It then updates the session cookies in the
        loader's context and verifies the login status by testing the login.

        Raises:
            SystemExit: If the cookies.sqlite file is not found or if the user is not
            logged in successfully in Firefox.
        """
        cookie_file = self.get_cookie_file()
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
        self.loader.context._session.cookies.update(cookie_data)
        username = self.loader.test_login()
        if not username:
            raise SystemExit(
                "Not logged in. Are you logged in successfully in Firefox?"
            )

        self.logger.info("Imported session cookie for '%s'.", username)
        self.loader.context.username = username  # type: ignore[assignment]

    def get_instagram_profile(self: "Instagram", username: str) -> Profile | None:
        """
        Retrieve the Instagram profile of a given user.

        Args:
            username (str): The username of the Instagram user.

        Returns:
            Profile | None: The Instagram profile of the user,
            or None if the profile doesn't exist.
        """
        try:
            profile: Profile = Profile.from_username(self.loader.context, username)
        except ProfileNotExistsException:
            self.logger.info("Profile '%s' not found.", username)
            return None
        return profile

    @staticmethod
    def get_cookie_file() -> str | None:
        """
        Retrieve the path to the Firefox cookies.sqlite file based on the system.

        This method determines the default location of the Firefox cookies.sqlite file
        for Windows, macOS (Darwin), and other Unix-like systems. It then uses glob to
        find the actual file path.

        Returns:
            str | None: The path to the cookies.sqlite file if found.

        Raises:
            SystemExit: If no cookies.sqlite file is found.
        """
        default_cookie_file = {
            "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
            "Darwin": "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
        }.get(system(), "~/.mozilla/firefox/*/cookies.sqlite")
        cookie_files = glob(expanduser(default_cookie_file))
        if not cookie_files:
            raise SystemExit("No Firefox cookies.sqlite file found.")
        return cookie_files[0]
