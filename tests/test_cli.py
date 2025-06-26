import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typer.testing import CliRunner

import cli  # Importar o módulo cli inteiro
from src.core.db import Base, Profile  # Importar Base, Profile

runner = CliRunner()


@pytest.fixture(name="db_session_cli")
def db_session_cli_fixture(monkeypatch: pytest.MonkeyPatch) -> Session:
    """Fixture for a in-memory SQLite database session for CLI tests."""
    engine = create_engine("sqlite:///:memory:")
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Monkeypatch _get_db_session em cli.py para usar o banco de dados de teste
    monkeypatch.setattr(cli, "_get_db_session", testing_session_local)  # PLW0108 corrigido

    Base.metadata.create_all(engine)  # Criar tabelas antes de cada teste
    with testing_session_local() as session:
        yield session
    Base.metadata.drop_all(engine)  # Remover tabelas depois de cada teste


def test_cli_list_empty(db_session_cli: Session) -> None:  # noqa: ARG001
    """Test 'list' command when no users are in the database."""
    result = runner.invoke(cli.app, ["list"])
    assert result.exit_code == 0
    assert "No rows" in result.stdout or (
        "Target Users" in result.stdout
        and "Username" in result.stdout
        and "Type" in result.stdout
        and "Full Name" in result.stdout
        and "Followers" in result.stdout
        and "Last Checked" in result.stdout
    )  # E501 corrigido


def test_cli_add_public_user(db_session_cli: Session) -> None:
    """Test 'add' command for a public user."""
    result = runner.invoke(cli.app, ["add", "testpublicuser"])
    assert result.exit_code == 0
    assert "User 'testpublicuser' added to the database as a public profile." in result.stdout

    profile = db_session_cli.query(Profile).filter_by(username="testpublicuser").first()
    assert profile is not None
    assert profile.username == "testpublicuser"
    assert not profile.is_private


def test_cli_add_private_user(db_session_cli: Session) -> None:
    """Test 'add' command for a private user."""
    result = runner.invoke(cli.app, ["add", "testprivateuser", "--private"])
    assert result.exit_code == 0
    assert "User 'testprivateuser' added to the database as a private profile." in result.stdout

    profile = db_session_cli.query(Profile).filter_by(username="testprivateuser").first()
    assert profile is not None
    assert profile.username == "testprivateuser"
    assert profile.is_private


def test_cli_add_existing_user(db_session_cli: Session) -> None:  # noqa: ARG001
    """Test 'add' command for an already existing user."""
    runner.invoke(cli.app, ["add", "existinguser"])
    result = runner.invoke(cli.app, ["add", "existinguser"])
    assert result.exit_code == 0
    assert "User 'existinguser' already exists in the database." in result.stdout


def test_cli_remove_user(db_session_cli: Session) -> None:
    """Test 'remove' command for an existing user."""
    runner.invoke(cli.app, ["add", "user_to_remove"])
    result = runner.invoke(cli.app, ["remove", "user_to_remove"])
    assert result.exit_code == 0
    assert "User 'user_to_remove' removed from the database." in result.stdout

    profile = db_session_cli.query(Profile).filter_by(username="user_to_remove").first()
    assert profile is None


def test_cli_remove_non_existing_user(db_session_cli: Session) -> None:  # noqa: ARG001
    """Test 'remove' command for a non-existing user."""
    result = runner.invoke(cli.app, ["remove", "nonexistinguser"])
    assert result.exit_code == 0
    assert "User 'nonexistinguser' not found in the database." in result.stdout


def test_cli_list_with_users(db_session_cli: Session) -> None:  # noqa: ARG001
    """Test 'list' command when users are in the database."""
    runner.invoke(cli.app, ["add", "user1"])
    runner.invoke(cli.app, ["add", "user2", "-p"])

    result = runner.invoke(cli.app, ["list"])
    assert result.exit_code == 0
    assert "user1" in result.stdout
    assert "Public" in result.stdout
    assert "user2" in result.stdout
    assert "Private" in result.stdout
