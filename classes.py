import logging
import time
from glob import glob
from os.path import expanduser
from pathlib import Path
from platform import system
from secrets import randbelow
from shutil import rmtree
from sqlite3 import OperationalError, connect

import instaloader
from instaloader import LatestStamps, Profile, ProfileNotExistsException, RateController
from tqdm import tqdm

import constants as const

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)


class MyRateController(RateController):
    def sleep(self, secs: float) -> None:
        time.sleep(secs + randbelow(8) + 15)


class Instagram:
    def __init__(self) -> None:
        self.download_directory = const.DOWNLOAD_DIRECTORY
        self.users = const.TARGET_USERS
        self.latest_stamps = self.__get_latest_stamps()
        self.loader = instaloader.Instaloader(
            dirname_pattern=str(self.download_directory),
            quiet=True,
            save_metadata=False,
            sanitize_paths=True,
            rate_controller=lambda ctx: MyRateController(ctx),
            fatal_status_codes=[429],
        )

    def run(self) -> None:
        self.__remove_all_txt()
        self.__import_session()
        self.download()

    def download(self) -> None:
        """
        Downloads Instagram profiles and their content.

        This method iterates over a list of users and downloads their profiles.
        It displays a progress bar to indicate the download progress. For each user,
        it fetches the Instagram profile and checks if the profile is private. If the
        profile is private, it only downloads the profile picture if it's new. If the
        profile is not private, it downloads the profile content including tagged posts
        and stories.
        """
        progress_bar = tqdm(
            self.users,
            desc="Downloading profiles",
            unit="profile",
            postfix={"user": None},
        )
        for user in progress_bar:
            progress_bar.set_postfix({"user": user})
            profile = self.__get_instagram_profile(user)
            if profile is None:
                continue
            if profile.is_private:
                self.loader.download_profilepic_if_new(profile, self.latest_stamps)
                continue

            self.loader.download_profiles(
                {profile},
                tagged=True,
                stories=True,
                latest_stamps=self.latest_stamps,
            )

    def __get_instagram_profile(self, user: str) -> Profile | None:
        """
        Retrieves the Instagram profile of a given user.

        Args:
            user (str): The username of the Instagram user.

        Returns:
            Profile | None: The Instagram profile of the user,
            or None if the profile does not exist.

        """
        try:
            profile: Profile = Profile.from_username(self.loader.context, user)
        except ProfileNotExistsException:
            tqdm.write(f"Profile {user} not found.")
            return None
        return profile

    def __get_latest_stamps(self) -> LatestStamps:
        """
        Retrieves the latest stamps for a given user.

        Returns:
            LatestStamps: An instance of the LatestStamps class.

        """
        stamps_path = Path(__file__).parent / "latest_stamps.ini"
        return instaloader.LatestStamps(stamps_path)

    def __remove_all_txt(self) -> None:
        """
        Removes all .txt files from the download directory.
        """
        for txt in self.download_directory.glob("*.txt"):
            rmtree(txt) if txt.is_dir() else txt.unlink()

    def __import_session(self) -> None:
        """
        Imports the session cookies from Firefox's cookies.sqlite file for Instagram.

        This method attempts to locate the Firefox cookies.sqlite file and extract
        cookies related to Instagram. It then updates the session cookies in the
        loader's context and verifies the login status by testing the login.

        Raises:
            SystemExit: If the cookies.sqlite file is not found or if the user is not
            logged in successfully in Firefox.

        """
        cookie_file = self.__get_cookiefile()
        if not cookie_file:
            msg = "No Firefox cookies.sqlite file found. Use -c COOKIEFILE."
            raise SystemExit(msg)
        logging.info("Using cookies from %s.", cookie_file)
        con = connect(f"file:{cookie_file}?immutable=1", uri=True)
        try:
            cookie_data = con.execute(
                "SELECT name, value FROM moz_cookies WHERE baseDomain='instagram.com'",
            )
        except OperationalError:
            cookie_data = con.execute(
                "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'",
            )
        self.loader.context._session.cookies.update(cookie_data)
        username = self.loader.test_login()
        if not username:
            msg = "Not logged in. Are you logged in successfully in Firefox?"
            raise SystemExit(msg)
        logging.info("Imported session cookie for %s.", username)
        self.loader.context.username = username  # type: ignore[assignment]

    @staticmethod
    def __get_cookiefile() -> str | None:
        """
        Retrieves the path to the Firefox cookies.sqlite file based on the system.

        This method determines the default location of the Firefox cookies.sqlite file
        for Windows, macOS (Darwin), and other Unix-like systems. It then uses glob to
        find the actual file path.

        Returns:
            Optional[str]: The path to the cookies.sqlite file if found.

        Raises:
            SystemExit: If no cookies.sqlite file is found.

        """
        default_cookiefile = {
            "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
            "Darwin": "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
        }.get(system(), "~/.mozilla/firefox/*/cookies.sqlite")
        cookie_files = glob(expanduser(default_cookiefile))
        if not cookie_files:
            msg = "No Firefox cookies.sqlite file found. Use -c COOKIEFILE."
            raise SystemExit(msg)
        return cookie_files[0]
