import json
import os
from pathlib import Path

from dotenv import load_dotenv

RESOURCES_DIRECTORY = Path(__file__).absolute().parents[2] / "src" / "resources"

load_dotenv(RESOURCES_DIRECTORY.parents[2])

DOWNLOAD_DIRECTORY = RESOURCES_DIRECTORY / "downloads"
DOWNLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

LOG_DIRECTORY = RESOURCES_DIRECTORY / "logs"
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

LATEST_STAMPS = RESOURCES_DIRECTORY / "latest_stamps.ini"

MAX_WORKERS = 16
BATCH_SIZE = 500

USER_TYPE_ENV_VAR = os.getenv("INSTALKER_USER_TYPE", "public").lower()
USER_FILENAME = f"{USER_TYPE_ENV_VAR}_users.json"


def load_target_users(filename: str) -> set[str]:
    """Load target users from the specified JSON file.

    :param filename: The name of the JSON file (e.g., "public_users.json").
    :type filename: str
    :return: Set of Instagram usernames to target.
    :rtype: set[str]
    """
    target_file = RESOURCES_DIRECTORY / "target" / filename

    try:
        with target_file.open(encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, FileNotFoundError):
        return set()


TARGET_USERS = load_target_users(USER_FILENAME)
