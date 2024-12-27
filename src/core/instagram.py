import logging
from glob import glob
from os.path import expanduser
from platform import system
from sqlite3 import OperationalError, connect

from instaloader import Instaloader, LatestStamps, Profile, ProfileNotExistsException
from tqdm import tqdm

from src import DOWNLOAD_DIRECTORY, LATEST_STAMPS, TARGET_USERS
from src.core.rate_controller import StealthRateController


class Instagram:
    """
    A class to manage Instagram profile downloads and session handling.
    """

    def __init__(
        self,
        users: set[str] | None = None,
    ) -> None:
        """
        Initialize the Instagram class with default settings and configurations.

        Args:
            users (set[str]): The set of Instagram usernames to download content from.
        """
        self.download_directory = DOWNLOAD_DIRECTORY
        self.users = users if users is not None else TARGET_USERS
        self.latest_stamps = LatestStamps(LATEST_STAMPS)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.loader = Instaloader(
            quiet=True,
            save_metadata=False,
            post_metadata_txt_pattern="",
            fatal_status_codes=[400],
            rate_controller=lambda ctx: StealthRateController(ctx),
        )
        self.logger.info(
            "Initialized Instagram downloader with %d users",
            len(self.users),
        )

    def run(self) -> None:
        """
        Execute the main sequence of operations for the class.
        """
        self._import_session()
        self._download()

    def _download(self) -> None:
        """
        Download Instagram profiles and their content.
        """
        self.logger.info("Starting download process for %d users", len(self.users))
        progress_bar = tqdm(
            self.users,
            desc="Downloading profiles",
            unit="profile",
        )
        for user in progress_bar:
            profile = self._get_instagram_profile(user)
            if not profile:
                continue

            progress_bar.set_postfix(
                user=user,
            )

            self.loader.dirname_pattern = str(DOWNLOAD_DIRECTORY / user)

            if profile.is_private and not profile.followed_by_viewer:
                self.logger.debug(
                    "Private profile - Only profile picture will be downloaded.",
                )
                self.loader.download_profilepic_if_new(profile, self.latest_stamps)
                continue

            self.loader.download_profiles(
                {profile},
                tagged=False,  # Unestable feature
                stories=True,
                reels=True,
                highlights=True,
                latest_stamps=self.latest_stamps,
            )

        self.logger.info("Download completed.")

    def _import_session(self) -> None:
        """
        Import the session cookies from Firefox's cookies.sqlite file for Instagram.
        """
        cookie_file = self._get_cookie_file()
        if not cookie_file:
            raise SystemExit("No Firefox cookies.sqlite file found.")

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

    def _get_instagram_profile(self, username: str) -> Profile | None:
        """
        Retrieve the Instagram profile of a given user.
        """
        try:
            profile = Profile.from_username(self.loader.context, username)
            if not isinstance(profile, Profile):
                self.logger.error("Unexpected type returned for profile '%s'", username)
                return None
            self.logger.debug(
                "Profile retrieved - Username: '%s', Followers: %d, Posts: %d",
                username,
                profile.followers,
                profile.mediacount,
            )
            return profile
        except ProfileNotExistsException:
            self.logger.info("Profile '%s' not found", username)
            return None
        except Exception as e:
            self.logger.error("Error retrieving profile '%s': %s", username, str(e))
            return None

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
