import time
from argparse import ArgumentParser
from glob import glob
from os.path import expanduser
from pathlib import Path
from platform import system
from random import randint
from shutil import rmtree
from sqlite3 import OperationalError, connect
from typing import Optional

import instaloader
from instaloader import LatestStamps, Profile, ProfileNotExistsException
from tqdm import tqdm

import constants as const


class MyRateController(instaloader.RateController):
    def __init__(self, context: instaloader.InstaloaderContext):
        super().__init__(context)
        self._earliest_next_request_time = randint(13, 20)
        self._iphone_earliest_next_request_time = randint(13, 20)

    def sleep(self, secs: float) -> None:
        time.sleep(secs + randint(13, 20))


class Instagram:
    def __init__(self) -> None:
        self.username = const.USERNAME
        self.download_directory = const.DOWNLOAD_DIRECTORY
        self.users = const.TARGET_USERS
        self.latest_stamps = self.__get_latest_stamps()
        self.loader = instaloader.Instaloader(
            dirname_pattern=str(self.download_directory),
            quiet=True,
            save_metadata=False,
            sanitize_paths=True,
            rate_controller=lambda ctx: MyRateController(ctx),
            fatal_status_codes=[400, 401, 404, 429],
        )
        self.remove_all_txt()
        self.import_session()

    def download(self) -> None:
        """
        Downloads Instagram profiles for the users in the set.
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
            time.sleep(randint(13, 20))
            if profile is None:
                continue
            if profile.is_private:
                self.loader.download_profilepic_if_new(profile, self.latest_stamps)
                continue

            self.loader.download_profiles(
                {profile},
                tagged=True,
                # igtv=True,
                # highlights=True,  # Latest stamps doesn't save highlights - 4.13.1
                stories=True,
                latest_stamps=self.latest_stamps,
            )

    def __get_instagram_profile(self, user: str) -> Optional[Profile]:
        """
        Retrieves the Instagram profile of a given user.

        Args:
            user (str): The username of the Instagram user.

        Returns:
            Optional[Profile]: The Instagram profile of the user,
            or None if the profile does not exist.
        """
        try:
            profile: Profile = Profile.from_username(self.loader.context, user)
            return profile
        except ProfileNotExistsException:
            print(f"Profile {user} not found.")
            return None

    def __get_latest_stamps(self) -> LatestStamps:
        """
        Retrieves the latest stamps for a given user.

        Returns:
            LatestStamps: An instance of the LatestStamps class.
        """
        stamps_path = Path(__file__).parent / "latest_stamps.ini"
        return instaloader.LatestStamps(stamps_path)

    def remove_all_txt(self) -> None:
        """
        Removes all .txt files from the download directory.

        Raises:
            OSError: If there is an error while removing the file.
        """
        for txt in self.download_directory.glob("*.txt"):
            try:
                rmtree(txt) if txt.is_dir() else txt.unlink()
            except OSError as e:
                print(f"Error: {e}")

    @staticmethod
    def __get_cookiefile() -> Optional[str]:
        default_cookiefile = {
            "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
            "Darwin": "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
        }.get(system(), "~/.mozilla/firefox/*/cookies.sqlite")
        cookiefiles = glob(expanduser(default_cookiefile))
        if not cookiefiles:
            raise SystemExit("No Firefox cookies.sqlite file found. Use -c COOKIEFILE.")
        return cookiefiles[0]

    def import_session(self) -> None:
        cookie_file = self.__get_cookiefile()
        if not cookie_file:
            raise SystemExit("No Firefox cookies.sqlite file found. Use -c COOKIEFILE.")
        print("Using cookies from {}.".format(cookie_file))
        conn = connect(f"file:{cookie_file}?immutable=1", uri=True)
        try:
            cookie_data = conn.execute(
                "SELECT name, value FROM moz_cookies WHERE baseDomain='instagram.com'"
            )
        except OperationalError:
            cookie_data = conn.execute(
                "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'"
            )
        self.loader.context._session.cookies.update(cookie_data)
        username = self.loader.test_login()
        if not username:
            raise SystemExit(
                "Not logged in. Are you logged in successfully in Firefox?"
            )
        print("Imported session cookie for {}.".format(username))
        self.loader.context.username = username  # type: ignore
        session_dir = const.SESSION_DIRECTORY
        session_dir.mkdir(exist_ok=True)
        session_file = str(const.SESSION_DIRECTORY / self.username)
        self.loader.save_session_to_file(session_file)
