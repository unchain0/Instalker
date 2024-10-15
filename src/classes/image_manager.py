"""Provides the ImageManager class for managing image files in a directory.

The ImageManager class allows for retrieval and removal of image files
based on their age.
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.constants import DOWNLOAD_DIRECTORY


class ImageManager:
    """Manages image files in a directory, retrieval and removal based on age."""

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

    def __init__(self) -> None:
        """Initialize the class with the download directory.

        Args:
            download_directory (Path): The directory to manage image files in.

        """
        self.download_directory = DOWNLOAD_DIRECTORY
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_media_files(self) -> list[Path]:
        """Get all the image files in the download directory and its subdirectories.

        Returns:
            list[Path]: A list of Path objects for the image files found.

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
        """Check if a file is older than the specified time.

        Args:
            file_path (Path): Full path to the file.
            time_delta (timedelta): Time duration to compare against.

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
        """Remove a specific file.

        Args:
            file_path (Path): Full path to the file.

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
        """Record a summary of the removals carried out.

        Args:
            removed_count (int): Number of files successfully removed.
            failed_removals (list[Path]): List of files that failed to be removed.

        """
        self.logger.info("Process completed. %d files removed.", removed_count)
        if failed_removals:
            self.logger.warning("Failed to remove %d files:", len(failed_removals))
            for failed_file in failed_removals:
                self.logger.warning(" - %s", failed_file)

    def remove_old_images(self, cutoff_delta: timedelta = timedelta(weeks=1)) -> None:
        """Remove media files in the that are older than the specified duration.

        Args:
            cutoff_delta (timedelta): The age limit for removing files.
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
