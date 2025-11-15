"""
Database configuration and session management.
"""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

# Database file path
DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "contacts.db"

# Create engine with expire_on_commit=False to allow access to objects outside session
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Create session factory with expire_on_commit=False
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(engine)


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.

    Usage:
        with get_db_session() as session:
            session.query(Contact).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
