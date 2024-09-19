import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from os.path import expanduser
from pathlib import Path
from platform import system
from secrets import randbelow
from shutil import rmtree
from sqlite3 import OperationalError, connect

import instaloader
from instaloader import LatestStamps, Profile, ProfileNotExistsException
from PIL import Image, UnidentifiedImageError
from tqdm import tqdm

import constants as const

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class MyRateController(instaloader.RateController):
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
        self.image_cleaner = ImageCleaner(self.download_directory)

    def run(self) -> None:
        self.__remove_all_txt()
        self.image_cleaner.remove_small_images()
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
            leave=False,
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
            Profile | None: The Instagram profile of the user, or None if the profile does not exist.

        """
        try:
            profile: Profile = Profile.from_username(self.loader.context, user)
        except ProfileNotExistsException:
            logging.warning("Profile %s not found.", user)
            return None
        else:
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
        If the login is successful, it saves the session to a file.

        Raises:
            SystemExit: If the cookies.sqlite file is not found or if the user is not logged in successfully in Firefox.

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
        session_dir = const.SESSION_DIRECTORY
        session_dir.mkdir(exist_ok=True)
        session_file = str(const.SESSION_DIRECTORY / username)
        self.loader.save_session_to_file(session_file)

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


class ImageCleaner:
    MIN_DIMENSION: int = 256
    IMAGE_EXTENSIONS = re.compile(r"\.(jpg|png|webp)$", re.IGNORECASE)

    def __init__(self, download_directory: Path) -> None:
        self.download_directory = download_directory

    def remove_small_images(self) -> None:
        """
        Removes all image files with dimensions smaller than 256x256 pixels from the download directory.
        """
        logging.info(
            "Starting to remove small images from the download directory.",
        )

        image_files = self.__get_image_files()

        with ThreadPoolExecutor() as executor:
            executor.map(self.__process_image, image_files)

    def __get_image_files(self) -> list[Path]:
        """
        Gets the list of image files in the download directory that match the valid extensions.
        """
        return [
            file_path
            for file_path in self.download_directory.glob("*")
            if self.IMAGE_EXTENSIONS.search(str(file_path))
        ]

    def __process_image(self, image_file: Path) -> None:
        """
        Processes an image file by checking its dimensions and deleting it if it is small or invalid.

        Args:
            image_file (Path): The path to the image file to be processed.

        """
        try:
            with Image.open(image_file) as img:
                if img.width < self.MIN_DIMENSION or img.height < self.MIN_DIMENSION:
                    logging.info(
                        "Removendo imagem pequena: %s (Dimensões: %dx%d)",
                        image_file,
                        img.width,
                        img.height,
                    )
                    image_file.unlink()
        except UnidentifiedImageError:
            logging.warning(
                "Arquivo não identificado como imagem, removendo: %s",
                image_file,
            )
            image_file.unlink()
