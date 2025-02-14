"""Provides the FileManager class for managing file operations in a directory.

It includes functionality to remove old files and files smaller than
specified dimensions.
"""

import concurrent.futures
import imghdr
import logging
import os
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path

from PIL import Image

from src import DOWNLOAD_DIRECTORY


class FileManager:
    """Manages files in a directory, retrieval and removal based on age."""

    SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".mpeg", ".mpg", ".mp4", ".webp")

    def __init__(self) -> None:
        """Initialize the class with the download directory."""
        self.download_directory = DOWNLOAD_DIRECTORY
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            "Initialized FileManager with directory: %s",
            self.download_directory,
        )
        self.media_files = self._get_files()

    def remove_old_files(self, cutoff_delta: timedelta = timedelta(days=30)) -> None:
        """Remove files in the directory that are older than the specified duration."""
        self.logger.info(
            "Starting removal of media older than %s days",
            cutoff_delta.days,
        )
        removed_count = 0
        failed_removals: list[Path] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(
                partial(self._process_old_file, cutoff_delta=cutoff_delta),
                self.media_files,
            )

        for status, file_path in results:
            if status == "removed":
                removed_count += 1
            elif status == "failed":
                failed_removals.append(file_path)

        self._log_removal_summary(removed_count, failed_removals)

    def _process_old_file(
        self,
        file_path: Path,
        cutoff_delta: timedelta,
    ) -> tuple[str, Path]:
        try:
            if self._is_file_older_than(file_path, cutoff_delta):
                if self._remove_file(file_path):
                    return ("removed", file_path)
                return ("failed", file_path)
        except Exception:
            self.logger.exception("Error processing file %s", file_path)
            return ("failed", file_path)
        else:
            return ("skipped", file_path)

    def remove_small_files(self, min_size: tuple[int, int]) -> None:
        """Remove files que são menores da dimensão fornecida, em paralelo."""
        self.logger.info(
            "Starting removal of files smaller than %dx%d",
            min_size[0],
            min_size[1],
        )
        files = self._get_files()
        removed_count = 0
        failed_removals: list[Path] = []

        with concurrent.futures.ThreadPoolExecutor() as executor:

            def process_file(file: Path) -> tuple[str, Path]:
                return self._process_small_file(file, min_size)

            results = executor.map(process_file, files)

        for status, file_path in results:
            if status == "removed":
                removed_count += 1
            elif status == "failed":
                failed_removals.append(file_path)

        self._log_removal_summary(removed_count, failed_removals)

    def _process_small_file(
        self,
        file_path: Path,
        min_size: tuple[int, int],
    ) -> tuple[str, Path]:
        try:
            if not imghdr.what(file_path):
                return ("skipped", file_path)

            with Image.open(file_path) as img:
                width, height = img.size

            if width >= min_size[0] and height >= min_size[1]:
                return ("skipped", file_path)

            if not self._remove_file(file_path):
                return ("failed", file_path)
        except Exception:
            self.logger.exception("Error processing file %s", file_path)
            return ("failed", file_path)
        else:
            return ("removed", file_path)

    def _get_files(self) -> list[Path]:
        """Get all the media files in the download directory and its subdirectories.

        Returns:
            list[Path]: A list of Path objects for the media files found.

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
            bool: True if the file is older than the time delta; False otherwise.

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
            bool: True if the file was removed successfully; False otherwise.

        """
        try:
            file_path.unlink()
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
            "Process completed, %d files removed out of %d",
            removed_count,
            len(self.media_files),
        )
        if failed_removals:
            for file in failed_removals:
                self.logger.warning(file)
            self.logger.warning("Failed to remove %d files", len(failed_removals))
