from dataclasses import dataclass
from pathlib import Path
from random import randint
from shutil import rmtree
from time import sleep
from typing import Optional, Set

import instaloader
from instaloader import LatestStamps, Profile, ProfileNotExistsException
from tqdm import tqdm

import utils.constants as const
from models.MyRateController import MyRateController


@dataclass
class InstagramProfile:
    profile: Profile
    latest_stamps: LatestStamps


class Instagram:
    def __init__(self, *, users: Set[str]):
        self.username = const.USERNAME
        self.password = const.PASSWORD
        self.download_directory = const.DOWNLOAD_DIRECTORY
        self.users = users
        self.loader = instaloader.Instaloader(
            quiet=True,
            dirname_pattern=str(self.download_directory),
            save_metadata=False,
            compress_json=False,
            rate_controller=lambda ctx: MyRateController(ctx),
            sanitize_paths=True,
        )
        self.__remove_all_txt()
        self.loader.login(user=self.username, passwd=self.password)

    def download(self) -> None:
        """
        Downloads Instagram profiles for the given users.
        """
        for user in tqdm(
            self.users,
            desc="Downloading profiles",
            unit="profile",
            leave=False,
        ):
            instagram_profile = self.__get_instagram_profile(user)
            sleep(randint(13, 20))
            if not instagram_profile:
                continue

            profile, latest_stamps = (
                instagram_profile.profile,
                instagram_profile.latest_stamps,
            )
            if profile.is_private:
                continue

            self.loader.download_profiles(
                {profile},
                tagged=True,
                # igtv=True,
                # highlights=True,  # Latest stamps doesn't save data >>> 4.13.1
                stories=True,
                latest_stamps=latest_stamps,
            )

    def __get_instagram_profile(self, user: str) -> Optional[InstagramProfile]:
        """
        Retrieves the Instagram profile of a given user.

        Args:
            user (str): The username of the Instagram profile to retrieve.

        Returns:
            Optional[InstagramProfile]: An instance of the InstagramProfile class,
            or None if the profile does not exist.
        """
        try:
            profile = Profile.from_username(self.loader.context, user)
            latest_stamps = self.__get_latest_stamps(user)
            return InstagramProfile(profile=profile, latest_stamps=latest_stamps)
        except ProfileNotExistsException:
            print(f"Profile {user} not found.")
            return None

    def __get_latest_stamps(self, user: str) -> LatestStamps:
        """
        Retrieves the latest stamps for a given user.

        Args:
            user (str): The username of the user.

        Returns:
            LatestStamps: An instance of the LatestStamps class.
        """
        stamps_path = Path(self.download_directory) / f"{user}.ini"
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
