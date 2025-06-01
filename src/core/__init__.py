from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from src.core.db import Profile, SessionLocal, init_db
from src.core.file_manager import FileManager
from src.core.instagram import Instagram
from src.utils.logger import setup_logging

logger = setup_logging()


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations for the main loop."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.exception("Main processing session error occurred. Rolling back.")
        db.rollback()
        raise
    finally:
        db.close()


__all__ = ["FileManager", "Instagram", "Profile", "get_session", "init_db"]
