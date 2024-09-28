import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path


class ImageManager:
    SUPPORTED_EXTENSIONS = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".flv",
        ".wmv",
        ".mpeg",
        ".mpg",
    )

    def __init__(self, download_directory: Path) -> None:
        """
        Initializes the class with the download directory.

        :param download_directory: Path to the directory where the images are stored.
        """
        self.download_directory = download_directory
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_media_files(self) -> list[Path]:
        """
        Gets all the image files in the download directory and its subdirectories.

        :return: List of full paths to image files.
        """
        media_files = [
            Path(root) / file
            for root, _, files in os.walk(self.download_directory)
            for file in files
            if file.lower().endswith(self.SUPPORTED_EXTENSIONS)
        ]
        self.logger.debug("Found %d media files.", len(media_files))
        return media_files

    def is_file_older_than(self, file_path: Path, time_delta: timedelta) -> bool:
        """
        Checks if a file is older than the specified time.

        :param file_path: Full path to the file.
        :param time_delta: timedelta object representing the age limit.
        :return: True if the file is older than time_delta, False otherwise.
        """
        try:
            file_mod_time = datetime.fromtimestamp(
                file_path.stat().st_mtime,
                tz=UTC,
            )
            cutoff_time = datetime.now(tz=UTC) - time_delta
            is_older = file_mod_time < cutoff_time
        except Exception:
            self.logger.exception(
                "Error getting the modification date for '%s'",
                file_path,
            )
            return False
        else:
            return is_older

    def remove_file(self, file_path: Path) -> bool:
        """
        Removes a specific file.

        :param file_path: Full path to the file.
        :return: True if removal was successful, False otherwise.
        """
        try:
            file_path.unlink()
            self.logger.debug("Image removed: '%s'", file_path)
        except Exception:
            self.logger.exception("Error removing file '%s'", file_path)
            return False
        else:
            return True

    def log_removal_summary(
        self,
        removed_count: int,
        failed_removals: list[Path],
    ) -> None:
        """
        Records a summary of the removals carried out.

        :param removed_count: Number of files successfully removed.
        :param failed_removals: List of file paths that failed to be removed.
        """
        self.logger.info("Process completed. %d files removed.", removed_count)
        if failed_removals:
            self.logger.warning("Failed to remove %d files:", len(failed_removals))
            for failed_file in failed_removals:
                self.logger.warning(" - %s", failed_file)

    def remove_old_images(self, cutoff_delta: timedelta = timedelta(weeks=1)) -> None:
        """
        Removes media files in the download directory that are older than the specified duration.

        Args:
            cutoff_delta (timedelta, optional): The age limit for removing files.
                                                Default is one week (timedelta(weeks=1)).

        """
        media_files = self.get_media_files()
        removed_count = 0
        failed_removals = []

        for file_path in media_files:
            if self.is_file_older_than(file_path, cutoff_delta):
                if self.remove_file(file_path):
                    removed_count += 1
                else:
                    failed_removals.append(file_path)

        self.log_removal_summary(removed_count, failed_removals)
