import json
import logging
from pathlib import Path

logger = logging.getLogger()

RESOURCES_DIRECTORY: Path = Path(__file__).absolute().parents[2] / "src" / "resources"

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
            return set(json.load(f))
    except json.JSONDecodeError:
        logger.exception("Error: The file %s contains invalid JSON.", target_file)
        return set()


TARGET_USERS: set[str] = load_target_users()
