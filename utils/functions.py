import os
from datetime import datetime
from pathlib import Path
from shutil import rmtree

from dotenv import load_dotenv
from pydantic import DirectoryPath


def prefix_ic() -> str:
    """
    Returns a string representing the current timestamp with a prefix.

    :return: The formatted string with the current timestamp and a prefix.
    """
    return f'{datetime.now().strftime("%H:%M:%S")} |> '


def load_env() -> dict[str, str]:
    """
    Load environment variables from an env file.

    :return: A dictionary with the environment variables.
    """
    project_dir = Path(__file__).parent.parent
    env_file = project_dir / ".env"

    if not os.path.exists(env_file):
        os.makedirs(env_file)

    load_dotenv(dotenv_path=env_file)

    return {
        "USER": os.getenv("USER"),
        "PASSWORD": os.getenv("PASSWORD"),
        "DOWNLOAD_DIR": os.getenv("DOWNLOAD_DIR"),
    }


def remove_all_txt(download_dir: DirectoryPath):
    """
    Remove all files with .txt extension from the specified directory.

    :param download_dir: Directory path where the text files are located.
    """
    for txt in Path(str(download_dir)).glob("*.txt"):
        try:
            rmtree(txt) if txt.is_dir() else txt.unlink()
        except Exception as e:
            print(f"Error to exclude {txt}: {e}")
