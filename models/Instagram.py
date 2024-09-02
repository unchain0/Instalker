from pathlib import Path
from random import random
from shutil import rmtree
from time import sleep
from typing import Optional, Set

import instaloader
from instaloader import LatestStamps, Profile, ProfileNotExistsException

import utils.constants as const
from models.MyRateController import MyRateController


class Instagram:
    def __init__(self, *, users: Set[str]):
        self.username = const.USERNAME
        self.password = const.PASSWORD
        self.download_directory = const.DOWNLOAD_DIRECTORY
        self.session_directory = const.SESSION_DIRECTORY
        self.log_directory = const.LOG_DIRECTORY
        self.users = users
        self.loader = instaloader.Instaloader(
            dirname_pattern=str(self.download_directory),
            save_metadata=False,
            compress_json=False,
            rate_controller=lambda ctx: MyRateController(ctx),
        )

    def get_instagram_profile(self, username: str) -> Optional[Profile]:
        """
        :param username: The Instagram username of the profile to be fetched.
        :return: An Optional[Profile] object corresponding to the username provided.
        """
        try:
            return Profile.from_username(self.loader.context, username)
        except ProfileNotExistsException:
            print(f"This profile doesn't exist >>> {username}")

    def get_latest_stamps(self, user: str) -> LatestStamps:
        """
        :param user: Username as a string to get the latest stamps for.
        :return: An instance of LatestStamps containing the latest stamps data.
        """
        stamps_path = Path(self.download_directory) / f"{user}.ini"
        return instaloader.LatestStamps(stamps_path)

    def log_in(self):
        """
        Logs in the user by either loading an existing session or creating a new one.

        If a session file corresponding to the username is found, it loads the session from the file.

        Otherwise, it logs in using the provided username and password and then saves the session to a file.
        """
        session_file = str(self.session_directory / self.username)
        try:
            self.loader.load_session_from_file(self.username, session_file)
        except FileNotFoundError:
            self.loader.login(user=self.username, passwd=self.password)
            self.loader.save_session_to_file(session_file)

    def download(self):
        """
        Download the Instagram profile pictures and associated media for the users in the user list.

        The method iterates through `self.users`, retrieves the latest download timestamps, and fetches the Instagram
        profile for each user.

        Depending on the profile's privacy settings and the loader's login status, the method handles downloading the
        profile picture and other media.
        """
        for user in self.users:
            latest_stamps = self.get_latest_stamps(user)
            profile = self.get_instagram_profile(user)

            if not profile:
                break

            sleep(const.TIMER + random())

            if not self.loader.context.is_logged_in:
                self.loader.download_profiles(
                    {profile},
                    tagged=True,
                    igtv=True,
                    latest_stamps=latest_stamps,
                )
                continue

            self.loader.download_profiles(
                {profile},
                tagged=True,  # igtv=True,  # KeyError: 'edge_felix_video_timeline'
                # highlights=True,  # Latest stamps doesn't save data >>> 4.13.1
                stories=True,
                latest_stamps=latest_stamps,
            )

    def remove_all_txt(self):
        """
        Removes all .txt files from the download directory.

        The method traverses the download directory for files and
        directories with a .txt extension and attempts to delete them.

        If an error occurs during the deletion process, it prints an error message.
        """
        for txt in self.download_directory.glob("*.txt"):
            try:
                rmtree(txt) if txt.is_dir() else txt.unlink()
            except Exception as e:
                print(f"Error to exclude {txt}: {e}")
