"""Provides the FileManager class for managing file operations in a directory.

It includes functionality to remove old files and files smaller than
specified dimensions.
"""

import concurrent.futures
import logging
import os
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import ClassVar, Literal

from src import DOWNLOAD_DIRECTORY
from src.config.settings import MAX_WORKERS

FileStatus = Literal["removed", "failed", "skipped"]
FileResult = tuple[FileStatus, Path]


class FileManager:
    """Manages files in a directory providing methods for retrieval and removal.

    This class handles operations on media files including:
    - Identifying and cataloging media files in directories
    - Removing old files based on modification time
    - Removing image files that don't meet minimum dimension requirements
    """

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".mpeg",
        ".mpg",
        ".mp4",
        ".webp",
    }
    IMAGE_EXTENSIONS: ClassVar[set[str]] = {".jpg", ".jpeg", ".png", ".webp"}
    LARGE_FILE_THRESHOLD: ClassVar[int] = 100_000

    def __init__(self) -> None:
        """Initialize the FileManager with the download directory."""
        self.download_directory = DOWNLOAD_DIRECTORY
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            "Initialized FileManager with directory: %s",
            self.download_directory,
        )
        self.media_files = self._get_files()

    def remove_old_files(self, cutoff_delta: timedelta = timedelta(days=30)) -> None:
        """Remove files older than the specified duration.

        :param cutoff_delta: Time duration threshold for file age.
        :type cutoff_delta: timedelta
        """
        self.logger.info(
            "Starting removal of media older than %s days",
            cutoff_delta.days,
        )

        removed_count = 0
        failed_removals: list[Path] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(
                executor.map(
                    partial(self._process_old_file, cutoff_delta=cutoff_delta),
                    self.media_files,
                )
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
    ) -> FileResult:
        """Process a file to check if it should be removed based on age.

        :param file_path: Path to the file to check.
        :type file_path: Path
        :param cutoff_delta: Time duration threshold.
        :type cutoff_delta: timedelta
        :return: Status of the operation and the file path.
        :rtype: FileResult
        """
        try:
            if self._is_file_older_than(file_path, cutoff_delta):
                if self._remove_file(file_path):
                    return ("removed", file_path)
                return ("failed", file_path)
        except (FileNotFoundError, PermissionError, OSError):
            self.logger.exception("Error processing file %s", file_path)
            return ("failed", file_path)
        else:
            return ("skipped", file_path)

    def _get_files(self) -> list[Path]:
        """Get all media files in the download directory and its subdirectories.

        :return: List of Path objects for the media files found.
        :rtype: list[Path]
        """
        media_files = []
        problematic_files = []

        for root, _, files in os.walk(self.download_directory):
            root_path = Path(root)
            for file in files:
                try:
                    file_path = root_path / file
                    suffix = Path(file).suffix.lower()
                    if suffix in self.SUPPORTED_EXTENSIONS:
                        try:
                            _ = file_path.stat()
                            media_files.append(file_path)
                        except OSError:
                            problematic_files.append(str(file_path))
                except OSError as e:
                    self.logger.warning(
                        "Error processing file '%s': %s",
                        root_path / file,
                        e,
                    )

        if problematic_files:
            self.logger.warning(
                "Found %d files with problematic names or access issues",
                len(problematic_files),
            )

        self.logger.debug("Found %d media files.", len(media_files))
        return media_files

    def _is_file_older_than(
        self,
        file_path: Path,
        time_delta: timedelta,
    ) -> bool:
        """Check if a file is older than the specified time.

        :param file_path: Path to the file.
        :type file_path: Path
        :param time_delta: Time duration to compare against.
        :type time_delta: timedelta
        :return: True if the file is older than the time delta.
        :rtype: bool
        """
        try:
            cutoff_time = datetime.now(tz=UTC) - time_delta

            try:
                file_stat = file_path.stat()
                if file_stat.st_mtime <= 0:
                    self.logger.warning("Invalid modification time for file: %s", file_path)
                    return False

                file_mod_time = datetime.fromtimestamp(file_stat.st_mtime, tz=UTC)
            except OSError:
                try:
                    file_stat = file_path.stat()
                    if file_stat.st_mtime <= 0:
                        self.logger.warning("Invalid modification time for file: %s", file_path)
                        return False

                    file_mod_time = datetime.fromtimestamp(file_stat.st_mtime, tz=UTC)
                except (OSError, ValueError):
                    self.logger.exception(
                        "Error getting the modification date for '%s'",
                        file_path,
                    )
                    return False
                else:
                    return file_mod_time < cutoff_time
            else:
                return file_mod_time < cutoff_time

        except (OSError, ValueError):
            self.logger.exception("Error getting the modification date for '%s'", file_path)
            return False

    def _remove_file(self, file_path: Path) -> bool:
        """Remove a specific file safely.

        :param file_path: Full path to the file.
        :type file_path: Path
        :return: True if the file was removed successfully; False otherwise.
        :rtype: bool
        """
        if not file_path.exists():
            self.logger.warning("File no longer exists: %s", file_path)
            return True

        try:
            file_path.unlink()
        except PermissionError:
            self.logger.exception("Permission denied when removing file: %s", file_path)
            try:
                file_path.unlink()
            except (OSError, PermissionError):
                return False
            else:
                return True
        except Exception:
            self.logger.exception("Error removing file: %s", file_path)
            return False
        else:
            return True

    def _log_removal_summary(
        self,
        removed_count: int,
        failed_removals: list[Path],
    ) -> None:
        """Record a summary of the removals carried out.

        :param removed_count: Number of files successfully removed.
        :type removed_count: int
        :param failed_removals: List of files that failed to be removed.
        :type failed_removals: list[Path]
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

    def get_storage_stats(self) -> dict[str, int | float | dict[str, int]]:
        """Get statistics about the files in the download directory.

        :return: Dictionary with statistics like total size, file count, etc.
        :rtype: dict
        """
        total_size = 0
        count_by_extension: dict[str, int] = {}

        for file_path in self.media_files:
            try:
                size = file_path.stat().st_size
                total_size += size

                # Count files by extension
                ext = file_path.suffix.lower()
                if ext in count_by_extension:
                    count_by_extension[ext] += 1
                else:
                    count_by_extension[ext] = 1
            except Exception:
                self.logger.exception("Error getting stats for %s", file_path)

        return {
            "total_files": len(self.media_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files_by_extension": count_by_extension,
        }

    def refresh(self) -> None:
        """Refresh the media files list.

        Call this method when files have been added or removed externally.
        """
        self.logger.info("Refreshing media files list")
        self.media_files = self._get_files()
        self.logger.info("Found %d media files after refresh", len(self.media_files))
