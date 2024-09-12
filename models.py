import time
from pathlib import Path
from random import randint
from shutil import rmtree
from typing import Optional

import instaloader
from instaloader import LatestStamps, Profile, ProfileNotExistsException
from tqdm import tqdm

import constants as const


class MyRateController(instaloader.RateController):
    def sleep(self, secs: float) -> None:
        time.sleep(secs + randint(13, 20))


class Instagram:
    def __init__(self) -> None:
        self.username = const.USERNAME
        self.password = const.PASSWORD
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
        self.__remove_all_txt()
        self.loader.login(user=self.username, passwd=self.password)

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

    def __remove_all_txt(self) -> None:
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

    def __str__(self) -> str:
        return f"Logged as {self.loader.context.username}"
