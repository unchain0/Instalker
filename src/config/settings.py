"""Settings configuration for the Instalker application.

Module manages all configuration settings with support for environment variables
and custom configuration files.
"""

import json
from pathlib import Path

RESOURCES_DIRECTORY: Path = Path(__file__).parents[2] / "src" / "resources"

DOWNLOAD_DIRECTORY: Path = RESOURCES_DIRECTORY / "downloads"
DOWNLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

LOG_DIRECTORY: Path = RESOURCES_DIRECTORY / "logs"
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

LATEST_STAMPS: Path = RESOURCES_DIRECTORY / "latest_stamps.ini"

MAX_WORKERS: int = 16
BATCH_SIZE: int = 500


def load_target_users() -> set[str]:
    """Load target users from the configuration file.

    :return: Set of Instagram usernames to target.
    :rtype: set[str]
    """
    target_file = RESOURCES_DIRECTORY / "target" / "users.json"

    try:
        with Path.open(target_file, encoding="utf-8") as f:
            users = set(json.load(f))
            return users
    except json.JSONDecodeError:
        print(f"Error: The file {target_file} contains invalid JSON.")
        return set()


TARGET_USERS: set[str] = load_target_users()
