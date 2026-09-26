"""Shared database base and utilities."""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./taskflow.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@contextmanager
def get_db():
    """Get database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables(engine):
    """Create all tables in the correct order."""
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """Drop all tables in the correct order."""
    Base.metadata.drop_all(bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)