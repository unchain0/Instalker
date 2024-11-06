from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from instaloader import Profile, ProfileNotExistsException

from src.core.instagram import Instagram


@pytest.fixture
def instagram_instance() -> Generator[Instagram, None, None]:
    with patch("instaloader.Instaloader"), patch("logging.getLogger"):
        yield Instagram(users={"test_user"})


@pytest.fixture
def mock_profile() -> MagicMock:
    profile = MagicMock(spec=Profile)
    profile.is_private = False
    profile.followed_by_viewer = True
    return profile


def test_instagram_init_with_custom_users() -> None:
    custom_users = {"user1", "user2"}
    with patch("instaloader.Instaloader"), patch("logging.getLogger"):
        instagram = Instagram(users=custom_users)
        assert instagram.users == custom_users


def test_instagram_init_with_default_users() -> None:
    with (
        patch("instaloader.Instaloader"),
        patch("logging.getLogger"),
        patch("src.core.instagram.TARGET_USERS", {"default_user"}),
    ):
        instagram = Instagram(users=None)
        assert instagram.users == {"default_user"}


def test_get_instagram_profile_existing(
    instagram_instance: Instagram,
    mock_profile: MagicMock,
) -> None:
    with patch("instaloader.Profile.from_username", return_value=mock_profile):
        profile = instagram_instance.get_instagram_profile("existing_user")
        assert profile == mock_profile


def test_get_instagram_profile_nonexisting(instagram_instance: Instagram) -> None:
    with patch(
        "instaloader.Profile.from_username",
        side_effect=ProfileNotExistsException("Profile not found"),
    ):
        profile = instagram_instance.get_instagram_profile("nonexisting_user")
        assert profile is None


def test_remove_all_txt(instagram_instance: Instagram, tmp_path: Path) -> None:
    # Set the download_directory to the temporary path
    instagram_instance.download_directory = tmp_path

    # Create some '.txt' files and other files in the temporary directory
    txt_file1 = tmp_path / "file1.txt"
    txt_file2 = tmp_path / "file2.txt"
    other_file = tmp_path / "image.jpg"

    txt_file1.touch()
    txt_file2.touch()
    other_file.touch()

    # Ensure files are created
    assert txt_file1.exists()
    assert txt_file2.exists()
    assert other_file.exists()

    # Call the method under test
    instagram_instance.remove_all_txt()

    # Assert that '.txt' files are removed
    assert not txt_file1.exists()
    assert not txt_file2.exists()

    # Assert that other files remain
    assert other_file.exists()


def test_import_session_success(instagram_instance: Instagram) -> None:
    # Mock cookie data to be returned by conn.execute()
    mock_cookie_data = [("sessionid", "abc123def456")]

    # Create a mock connection object with an execute method
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_cookie_data

    with (
        patch.object(
            instagram_instance,
            "get_cookie_file",
            return_value="cookie_path",
        ),
        patch("src.core.instagram.connect", return_value=mock_conn) as mock_connect,
        patch.object(
            instagram_instance.loader.context._session.cookies,
            "update",
        ) as mock_update,
        patch.object(
            instagram_instance.loader,
            "test_login",
            return_value="test_user",
        ),
    ):
        instagram_instance.import_session()
        mock_connect.assert_called_once_with(
            "file:cookie_path?immutable=1",
            uri=True,
        )
        mock_conn.execute.assert_called()
        mock_update.assert_called_with(mock_cookie_data)
        assert instagram_instance.loader.context.username == "test_user"


def test_import_session_no_cookies(instagram_instance: Instagram) -> None:
    with (
        patch.object(instagram_instance, "get_cookie_file", return_value=None),
        pytest.raises(SystemExit),
    ):
        instagram_instance.import_session()


def test_download_private_profile_not_followed(
    instagram_instance: Instagram,
    mock_profile: MagicMock,
) -> None:
    mock_profile.is_private = True
    mock_profile.followed_by_viewer = False
    with (
        patch.object(
            instagram_instance,
            "get_instagram_profile",
            return_value=mock_profile,
        ),
        patch.object(
            instagram_instance.loader,
            "download_profilepic_if_new",
        ) as mock_download_profilepic,
        patch("tqdm.tqdm") as mock_tqdm,
    ):
        mock_tqdm.return_value = ["test_user"]
        instagram_instance.download()
        mock_download_profilepic.assert_called_once_with(
            mock_profile,
            instagram_instance.latest_stamps,
        )


def test_download_private_profile_followed(
    instagram_instance: Instagram,
    mock_profile: MagicMock,
) -> None:
    mock_profile.is_private = True
    mock_profile.followed_by_viewer = True
    with (
        patch.object(
            instagram_instance,
            "get_instagram_profile",
            return_value=mock_profile,
        ),
        patch.object(
            instagram_instance.loader,
            "download_profiles",
        ) as mock_download_profiles,
        patch("tqdm.tqdm") as mock_tqdm,
    ):
        mock_tqdm.return_value = ["test_user"]
        instagram_instance.download()
        mock_download_profiles.assert_called_once()


def test_download_public_profile(
    instagram_instance: Instagram,
    mock_profile: MagicMock,
) -> None:
    mock_profile.is_private = False
    with (
        patch.object(
            instagram_instance,
            "get_instagram_profile",
            return_value=mock_profile,
        ),
        patch.object(
            instagram_instance.loader,
            "download_profiles",
        ) as mock_download_profiles,
        patch("tqdm.tqdm") as mock_tqdm,
    ):
        mock_tqdm.return_value = ["test_user"]
        instagram_instance.download()
        mock_download_profiles.assert_called_once()


def test_run(instagram_instance: Instagram) -> None:
    with (
        patch.object(instagram_instance, "remove_all_txt") as mock_remove_all_txt,
        patch.object(instagram_instance, "import_session") as mock_import_session,
        patch.object(instagram_instance, "download") as mock_download,
    ):
        instagram_instance.run()
        mock_remove_all_txt.assert_called_once()
        mock_import_session.assert_called_once()
        mock_download.assert_called_once()
