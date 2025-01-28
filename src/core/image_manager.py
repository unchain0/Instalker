"""Provides the ImageManager class for managing image files in a directory.

It includes functionality to remove old images and images smaller than
specified dimensions.
"""

import imghdr
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from PIL import Image

from src import DOWNLOAD_DIRECTORY


class ImageManager:
    """Manages image files in a directory, retrieval and removal based on age."""

    SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".mpeg", ".mpg", ".mp4", ".webp")

    def __init__(self) -> None:
        """Initialize the class with the download directory."""
        self.download_directory = DOWNLOAD_DIRECTORY
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            "Initialized ImageManager with directory: %s",
            self.download_directory,
        )
        self.media_files = self._get_media_files()

    def remove_old_images(
        self,
        cutoff_delta: timedelta = timedelta(weeks=4),
    ) -> None:
        """Remove media files in the that are older than the specified duration.

        Args:
            cutoff_delta (timedelta): The age limit for removing files.

        """
        self.logger.info(
            "Starting removal of media older than %s days",
            cutoff_delta.days,
        )
        removed_count = 0
        failed_removals: list[Path] = []

        for file_path in self.media_files:
            if self._is_file_older_than(file_path, cutoff_delta):
                if self._remove_file(file_path):
                    removed_count += 1
                else:
                    failed_removals.append(file_path)

        self._log_removal_summary(removed_count, failed_removals)

    def remove_small_images(self, min_size: tuple[int, int]) -> None:
        """Remove images that are smaller than the specified dimensions.

        Args:
            min_size (tuple[int, int]): Minimum width and height in pixels.

        """
        self.logger.info(
            "Starting removal of images smaller than %dx%d",
            min_size[0],
            min_size[1],
        )
        media_files = self._get_media_files()
        removed_count = 0
        failed_removals: list[Path] = []

        for file_path in media_files:
            try:
                if not imghdr.what(file_path):
                    continue

                img = Image.open(file_path)
                width, height = img.size
                img.close()

                if width >= min_size[0] and height >= min_size[1]:
                    continue

                if not self._remove_file(file_path):
                    failed_removals.append(file_path)
                    continue

                removed_count += 1

            except Exception:
                err = f"Error processing image {file_path}"
                self.logger.exception(err)
                failed_removals.append(file_path)

        self._log_removal_summary(removed_count, failed_removals)

    def _get_media_files(self) -> list[Path]:
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

    def _is_file_older_than(
        self,
        file_path: Path,
        time_delta: timedelta,
    ) -> bool:
        """Check if a file is older than the specified time.

        Args:
            file_path (Path): Full path to the file.
            time_delta (timedelta): Time duration to compare against.

        Returns:
            bool: True if the file is older than the time delta. False otherwise.

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

    def _remove_file(self, file_path: Path) -> bool:
        """Remove a specific file.

        Args:
            file_path (Path): Full path to the file.

        Returns:
            bool: True if the file was removed successfully. False otherwise.

        """
        try:
            # This is a security risk, use os.remove instead
            Path.unlink(file_path)
            self.logger.debug("File removed: '%s'", file_path)
        except Exception:
            self.logger.exception("Error removing file '%s'", file_path)
            return False
        else:
            return True

    def _log_removal_summary(
        self,
        removed_count: int,
        failed_removals: list[Path],
    ) -> None:
        """Record a summary of the removals carried out.

        Args:
            removed_count (int): Number of files successfully removed.
            failed_removals (list[Path]): List of files that failed to be removed.

        """
        self.logger.info(
            "Process completed, %d files removed in %d",
            removed_count,
            len(self.media_files),
        )
        if failed_removals:
            for file in failed_removals:
                self.logger.warning(file)
            self.logger.warning("Failed to remove %d files:", len(failed_removals))
