import json
from pathlib import Path

SOURCE_DIRECTORY = Path(__file__).parent.parent / "resources"

DOWNLOAD_DIRECTORY = SOURCE_DIRECTORY / "downloads"
DOWNLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

LOG_DIRECTORY = SOURCE_DIRECTORY / "logs"
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

LATEST_STAMPS = SOURCE_DIRECTORY / "latest_stamps.ini"

with Path.open(SOURCE_DIRECTORY / "target" / "users.json") as f:
    TARGET_USERS: set[str] = set(json.load(f))
