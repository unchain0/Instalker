from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

USERNAME: str = os.environ["INSTA_USERNAME"]
PASSWORD: str = os.environ["INSTA_PASSWORD"]
DOWNLOAD_DIRECTORY: Path = Path(__file__).parent.parent / "downloads"
SESSION_DIRECTORY: Path = Path(__file__).parent.parent / "sessions"
