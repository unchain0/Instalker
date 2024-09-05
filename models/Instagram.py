from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

import instaloader
from instaloader import LatestStamps, Profile, ProfileNotExistsException
from tqdm import tqdm

import utils.constants as const


@dataclass
class InstagramProfile:
    profile: Profile
    latest_stamps: LatestStamps


class Instagram:
    def __init__(self, *, users: Set[str]):
        self.username = const.USERNAME
        self.password = const.PASSWORD
        self.download_directory = const.DOWNLOAD_DIRECTORY
        self.session_directory = const.SESSION_DIRECTORY
        self.log_directory = const.LOG_DIRECTORY
        self.users = users
        self.loader = instaloader.Instaloader(
            quiet=True,
            dirname_pattern=str(self.download_directory),
            save_metadata=False,
            compress_json=False,
            rate_controller=lambda ctx: instaloader.RateController(ctx),
            fatal_status_codes=[400, 429],
        )
        self.__log_in()

    def download(self) -> None:
        """
        Downloads Instagram profiles for the given users.
        """
        for user in tqdm(
            self.users,
            desc="Downloading profiles",
            unit="profile",
        ):
            instagram_profile = self.__get_instagram_profile(user)
            if not instagram_profile:
                break

            profile, latest_stamps = (
                instagram_profile.profile,
                instagram_profile.latest_stamps,
            )

            self.loader.download_profiles(
                {profile},
                tagged=True,
                # highlights=True,  # Latest stamps doesn't save data >>> 4.13.1
                stories=True,
                latest_stamps=latest_stamps,
            )

    def __log_in(self) -> None:
        """
        Logs in to Instagram using the provided username and password.
        """
        session_file = str(self.session_directory / self.username)
        Path(session_file).parent.mkdir(parents=True, exist_ok=True)
        try:
            self.loader.load_session_from_file(self.username, session_file)
        except FileNotFoundError:
            self.loader.login(user=self.username, passwd=self.password)
            self.loader.save_session_to_file(session_file)

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
