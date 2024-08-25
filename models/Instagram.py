import os
from pathlib import Path
from typing import Set

import instaloader
from pydantic import BaseModel, DirectoryPath, field_validator

import utils.functions as func

func.load_env()


class Instagram(BaseModel):
    login: bool = False
    users_set: Set[str] = {}
    loader: instaloader.Instaloader = None

    username: str = os.getenv("USER")
    password: str = os.getenv("PASSWORD")
    download_directory: DirectoryPath = os.getenv("DOWNLOAD_DIR")
    session_directory: DirectoryPath = Path(__file__).parent.parent / "sessions"

    def __init__(self):
        super().__init__()
        self.loader = instaloader.Instaloader(
            dirname_pattern=self.download_directory,
            save_metadata=False,
            compress_json=False,
            # rate_controller=lambda ctx: MyRateController(ctx),
        )

    # region Validators
    @field_validator("username")
    def check_user(cls, v: str) -> str:
        if len(v) < 2:
            raise ValueError("Username must contain at least 2 characters")
        return v

    @field_validator("password")
    def check_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must contain at least 6 characters")
        return v

    @field_validator("download_directory")
    def check_download_dir(cls, v: DirectoryPath) -> DirectoryPath:
        if not os.path.exists(v):
            raise ValueError("Download directory must be a valid directory")
        return v

    @field_validator("users_set")
    def check_list_users(cls, v: Set[str]) -> Set[str]:
        if not v:
            raise ValueError("Users set must contain at least one user")
        return v

    # endregion

    def log_in(self):
        if not self.log_in:
            return
        session_file = str(self.session_directory / self.username)
        try:
            self.loader.load_session_from_file(self.username, session_file)
        except FileNotFoundError:
            self.loader.login(user=self.username, passwd=self.password)
            self.loader.save_session_to_file(session_file)

    def download(self):
        for user in self.users_set:
            stamps_path = Path(self.download_directory) / f"{user}.ini"
            latest_stamps = instaloader.LatestStamps(stamps_path)
            profile = instaloader.Profile.from_username(self.loader.context, user)
            if not self.log_in:
                self.loader.download_profiles(
                    {profile},
                    profile_pic=True,
                    posts=True,
                    latest_stamps=latest_stamps,
                )
                continue
            self.loader.download_profiles(
                {profile},
                profile_pic=True,
                posts=True,
                tagged=True,
                # igtv=True,  # KeyError: 'edge_felix_video_timeline'
                # highlights=True,
                stories=True,
                latest_stamps=latest_stamps,
            )

    def __del__(self):
        func.remove_all_txt(self.download_directory)

    class Config:
        arbitrary_types_allowed = True
