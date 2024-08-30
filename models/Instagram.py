from pathlib import Path
from shutil import rmtree
from typing import Set

import instaloader

import utils.constants as const
from models.MyRateController import MyRateController


class Instagram:
    def __init__(self, users: Set[str]):
        self.username = const.USERNAME
        self.password = const.PASSWORD
        self.download_directory = const.DOWNLOAD_DIRECTORY
        self.session_directory = const.SESSION_DIRECTORY
        self.users = users

        self.loader = instaloader.Instaloader(
            dirname_pattern=str(self.download_directory),
            save_metadata=False,
            compress_json=False,
            rate_controller=lambda ctx: MyRateController(ctx),
        )
        self.__log_in()

    def __log_in(self):
        session_file = str(self.session_directory / self.username)
        try:
            self.loader.load_session_from_file(self.username, session_file)
        except FileNotFoundError:
            self.loader.login(user=self.username, passwd=self.password)
            self.loader.save_session_to_file(session_file)

    def download(self):
        for user in self.users:
            stamps_path = Path(self.download_directory) / f"{user}.ini"
            latest_stamps = instaloader.LatestStamps(stamps_path)
            profile = instaloader.Profile.from_username(self.loader.context, user)
            self.loader.download_profiles(
                {profile},
                profile_pic=True,
                posts=True,
                tagged=True,
                # igtv=True,  # KeyError: 'edge_felix_video_timeline'
                # highlights=True,  # Sometimes it can give KeyError
                stories=True,
                latest_stamps=latest_stamps,
            )

    def remove_all_txt(self):
        """
        Remove all files with .txt extension from the specified directory.
        """
        for txt in self.download_directory.glob("*.txt"):
            try:
                rmtree(txt) if txt.is_dir() else txt.unlink()
            except Exception as e:
                print(f"Error to exclude {txt}: {e}")

    class Config:
        arbitrary_types_allowed = True
