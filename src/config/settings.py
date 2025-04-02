"""Settings configuration for the Instalker application.

Module manages all configuration settings with support for environment variables
and custom configuration files.
"""

import json
import os
from pathlib import Path
from typing import Final, Set

SOURCE_DIRECTORY: Final[Path] = Path(__file__).parent.parent / "resources"

DOWNLOAD_DIRECTORY: Final[Path] = Path(
    os.environ.get("INSTALKER_DOWNLOAD_DIR", SOURCE_DIRECTORY / "downloads")
)
DOWNLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

LOG_DIRECTORY: Final[Path] = Path(
    os.environ.get("INSTALKER_LOG_DIR", SOURCE_DIRECTORY / "logs")
)
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

LATEST_STAMPS: Final[Path] = Path(
    os.environ.get(
        "INSTALKER_STAMPS_FILE", SOURCE_DIRECTORY / "latest_stamps.ini"
    )
)

MAX_WORKERS: Final[int] = int(os.environ.get("INSTALKER_MAX_WORKERS", "16"))
BATCH_SIZE: Final[int] = int(os.environ.get("INSTALKER_BATCH_SIZE", "500"))
DEFAULT_TIMEOUT: Final[int] = int(os.environ.get("INSTALKER_TIMEOUT", "100"))
MAX_CONNECTION_ATTEMPTS: Final[int] = int(
    os.environ.get("INSTALKER_MAX_CONNECTION", "10")
)


def load_target_users() -> Set[str]:
    """Load target users from the configuration file.

    Returns:
        Set of Instagram usernames to target
    """
    target_file = SOURCE_DIRECTORY / "target" / "users.json"

    try:
        with Path.open(target_file, encoding="utf-8") as f:
            users = set(json.load(f))
            return users
    except FileNotFoundError:
        # Create example file if it doesn't exist
        example_file = SOURCE_DIRECTORY / "target" / "users-example.json"
        if not example_file.exists():
            SOURCE_DIRECTORY.joinpath("target").mkdir(
                parents=True, exist_ok=True
            )
            with Path.open(example_file, "w", encoding="utf-8") as f:
                json.dump(["example_user1", "example_user2"], f, indent=2)
        return set()
    except json.JSONDecodeError:
        print(f"Error: The file {target_file} contains invalid JSON.")
        return set()


TARGET_USERS: Final[Set[str]] = load_target_users()
