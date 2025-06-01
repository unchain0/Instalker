import os
from collections.abc import Iterator
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.sql import func

load_dotenv()

# --- Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    err = "DATABASE_URL environment variable is not set."
    raise ValueError(err)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- SQLAlchemy Base Model ---
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# --- Association Tables ---
# Using SQLAlchemy Core Table for association tables (no separate model class needed)
profile_hashtags_association = Table(
    "profile_hashtags",
    Base.metadata,
    Column("profile_hashtag_id", BigInteger(), ForeignKey("profiles.id"), primary_key=True),
    Column("hashtag_id", BigInteger(), ForeignKey("hashtags.id"), primary_key=True),
)

profile_mentions_association = Table(
    "profile_mentions",
    Base.metadata,
    Column("profile_mention_id", BigInteger(), ForeignKey("profiles.id"), primary_key=True),
    Column("mention_id", BigInteger(), ForeignKey("mentions.id"), primary_key=True),
)


# --- SQLAlchemy Models ---
class Profile(Base):
    """SQLAlchemy model representing an Instagram profile."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String())
    biography: Mapped[str | None] = mapped_column(Text())
    followers: Mapped[int | None] = mapped_column(Integer())
    followees: Mapped[int | None] = mapped_column(Integer())
    post_count: Mapped[int | None] = mapped_column(Integer())
    business_category_name: Mapped[str | None] = mapped_column(String())
    external_url: Mapped[str | None] = mapped_column(String())
    is_private: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    blocked_by_viewer: Mapped[bool | None] = mapped_column(Boolean())
    followed_by_viewer: Mapped[bool | None] = mapped_column(Boolean())
    follows_viewer: Mapped[bool | None] = mapped_column(Boolean())
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    hashtags: Mapped[list["Hashtag"]] = relationship(
        secondary=profile_hashtags_association,
        back_populates="profiles",
        lazy="selectin",
    )
    mentions: Mapped[list["Mention"]] = relationship(
        secondary=profile_mentions_association,
        back_populates="profiles",
        lazy="selectin",
    )


class Hashtag(Base):
    """SQLAlchemy model representing a hashtag found in biographies."""

    __tablename__ = "hashtags"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    tag: Mapped[str] = mapped_column(String(), unique=True, index=True, nullable=False)

    # Relationship back to profiles
    profiles: Mapped[list["Profile"]] = relationship(
        secondary=profile_hashtags_association,
        back_populates="hashtags",
        lazy="selectin",
    )


class Mention(Base):
    """SQLAlchemy model representing a user mention found in biographies."""

    __tablename__ = "mentions"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    username: Mapped[str] = mapped_column(String(), unique=True, index=True, nullable=False)

    # Relationship back to profiles
    profiles: Mapped[list["Profile"]] = relationship(
        secondary=profile_mentions_association,
        back_populates="mentions",
        lazy="selectin",
    )


def get_db() -> Iterator[Session]:
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables."""
    Base.metadata.create_all(bind=engine)
