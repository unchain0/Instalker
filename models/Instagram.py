import os
from pathlib import Path
from typing import Set

import instaloader
from icecream import ic
from pydantic import BaseModel, DirectoryPath, field_validator

import utils.functions as func
from models.MyRateController import MyRateController

env = func.load_env()


class Instagram(BaseModel):
    login: bool = False
    list_users: Set[str] = {}
    L: instaloader.Instaloader = None

    user: str = env["USER"]
    password: str = env["PASSWORD"]
    download_dir: DirectoryPath = env["DOWNLOAD_DIR"]

    def __init__(self):
        super().__init__()

        self.L = instaloader.Instaloader(
            dirname_pattern=self.download_dir,
            save_metadata=False,
            rate_controller=lambda ctx: MyRateController(ctx),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36",
        )

        ic.prefix = func.prefix_ic()

        if self.login:
            self.L.login(user=self.user, passwd=self.password)

    # region Validators
    @field_validator("user")
    def check_user(cls, v: str) -> str:
        if len(v) < 2:
            raise ValueError("user must contain at least 2 characters")
        return v

    @field_validator("password")
    def check_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("password must contain at least 6 characters")
        return v

    @field_validator("download_dir")
    def check_download_dir(cls, v: DirectoryPath) -> DirectoryPath:
        if not os.path.exists(v):
            raise ValueError("download_dir must be a valid directory")
        return v

    @field_validator("list_users")
    def check_list_users(cls, v: Set[str]) -> Set[str]:
        if not v:
            raise ValueError("list_users must contain at least one user")
        return v

    # endregion

    def download(self):
        for user in self.list_users:
            ic(user)

            latest_stamps_path = Path(self.download_dir) / f"{user}.ini"
            latest_stamps = instaloader.LatestStamps(latest_stamps_path)

            profile = instaloader.Profile.from_username(self.L.context, user)

            if not self.login:
                self.L.download_profiles(
                    {profile}, tagged=True, latest_stamps=latest_stamps
                )
                continue

            self.L.download_profiles(
                {profile},
                tagged=True,
                # igtv=True,  # KeyError: 'edge_felix_video_timeline'
                highlights=True,
                stories=True,
                latest_stamps=latest_stamps,
            )

    def __del__(self):
        func.remove_all_txt(self.download_dir)

    class Config:
        arbitrary_types_allowed = True
