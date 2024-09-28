import json
from pathlib import Path

ROOT_DIRECTORY = Path(__file__).parent.parent

LOG_DIRECTORY = ROOT_DIRECTORY / "logs"
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

DOWNLOAD_DIRECTORY = ROOT_DIRECTORY / "downloads"
DOWNLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

with Path.open(ROOT_DIRECTORY / "target_users.json") as f:
    TARGET_USERS: list[str] = list(
        set(json.load(f)),
    )
