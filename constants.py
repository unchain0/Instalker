import json
from pathlib import Path

DOWNLOAD_DIRECTORY = Path(__file__).parent / "downloads"
with Path.open(Path(__file__).parent / "target_users.json") as f:
    TARGET_USERS: list[str] = json.load(f)
