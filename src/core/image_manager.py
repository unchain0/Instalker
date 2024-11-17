import imghdr
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from PIL import Image

from src import DOWNLOAD_DIRECTORY


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

    def __init__(self: "ImageManager") -> None:
        """
        Initialize the class with the download directory.

        Args:
            download_directory (Path): The directory to manage image files in.
        """
        self.download_directory = DOWNLOAD_DIRECTORY
        self.logger = logging.getLogger(self.__class__.__name__)

    def remove_old_images(
        self: "ImageManager",
        cutoff_delta: timedelta = timedelta(weeks=1),
    ) -> None:
        """
        Remove media files in the that are older than the specified duration.

        Args:
            cutoff_delta (timedelta): The age limit for removing files.
                Default is one week (timedelta(weeks=1)).
        """
        media_files = self.__get_media_files()
        removed_count = 0
        failed_removals = []

        for file_path in media_files:
            if self.__is_file_older_than(file_path, cutoff_delta):
                if self.__remove_file(file_path):
                    removed_count += 1
                else:
                    failed_removals.append(file_path)

        self.__log_removal_summary(removed_count, failed_removals)

    def remove_small_images(self: "ImageManager", min_size: tuple[int, int]) -> None:
        """
        Remove images that are smaller than the specified dimensions.

        Args:
            min_size (tuple[int, int]): Minimum width and height in pixels.
        """
        media_files = self.__get_media_files()
        removed_count = 0
        failed_removals = []

        for file_path in media_files:
            try:
                # Skip if not an image file (e.g., videos)
                if not imghdr.what(file_path):
                    continue

                img = Image.open(file_path)
                width, height = img.size
                img.close()  # Fecha o arquivo explicitamente

                if width < min_size[0] or height < min_size[1]:
                    if self.__remove_file(file_path):
                        removed_count += 1
                        self.logger.debug(
                            f"Removed small image: {file_path} ({width}x{height})"
                        )
                    else:
                        failed_removals.append(file_path)
            except Exception:
                self.logger.exception(f"Error processing image {file_path}")
                failed_removals.append(file_path)

        self.__log_removal_summary(removed_count, failed_removals)

    def __get_media_files(self: "ImageManager") -> list[Path]:
        """
        Get all the image files in the download directory and its subdirectories.

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

    def __is_file_older_than(
        self: "ImageManager",
        file_path: Path,
        time_delta: timedelta,
    ) -> bool:
        """
        Check if a file is older than the specified time.

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

    def __remove_file(self: "ImageManager", file_path: Path) -> bool:
        """
        Remove a specific file.

        Args:
            file_path (Path): Full path to the file.
        """
        try:
            os.unlink(file_path)
            self.logger.debug("File moved to Recycle Bin: '%s'", file_path)
        except Exception:
            self.logger.exception("Error removing file '%s'", file_path)
            return False
        else:
            return True

    def __log_removal_summary(
        self: "ImageManager",
        removed_count: int,
        failed_removals: list[Path],
    ) -> None:
        """
        Record a summary of the removals carried out.

        Args:
            removed_count (int): Number of files successfully removed.
            failed_removals (list[Path]): List of files that failed to be removed.
        """
        self.logger.info("Process completed. %d files removed.", removed_count)
        if failed_removals:
            self.logger.warning("Failed to remove %d files:", len(failed_removals))
            for failed_file in failed_removals:
                self.logger.warning(" - %s", failed_file)
