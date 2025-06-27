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
