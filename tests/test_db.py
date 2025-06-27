from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.db import Base, Profile


@pytest.fixture(name="db_session")
def db_session_fixture() -> Generator[Session, Any]:
    """Fixture for a in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    try:
        yield session
    finally:
        session.close()


def test_create_profile(db_session: Session) -> None:
    """Test creating a new profile."""
    profile = Profile(username="testuser", is_private=False)
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    assert profile.id is not None
    assert profile.username == "testuser"
    assert not profile.is_private


def test_get_profile(db_session: Session) -> None:
    """Test retrieving an existing profile."""
    profile = Profile(username="anotheruser", is_private=True)
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    retrieved_profile = db_session.query(Profile).filter_by(username="anotheruser").first()
    assert retrieved_profile is not None
    assert retrieved_profile.username == "anotheruser"
    assert retrieved_profile.is_private


def test_update_profile(db_session: Session) -> None:
    """Test updating an existing profile."""
    profile = Profile(username="updateuser", is_private=False)
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    profile.is_private = True
    profile.full_name = "Update User"
    db_session.commit()
    db_session.refresh(profile)

    updated_profile = db_session.query(Profile).filter_by(username="updateuser").first()
    assert updated_profile is not None
    assert updated_profile.is_private
    assert updated_profile.full_name == "Update User"


def test_delete_profile(db_session: Session) -> None:
    """Test deleting a profile."""
    profile = Profile(username="deleteuser", is_private=False)
    db_session.add(profile)
    db_session.commit()

    db_session.delete(profile)
    db_session.commit()

    deleted_profile = db_session.query(Profile).filter_by(username="deleteuser").first()
    assert deleted_profile is None
