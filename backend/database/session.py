"""
Database session management using SQLAlchemy async engine.
Provides get_db() dependency for FastAPI routes.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from backend.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# Ensure the data directory exists before creating the engine
Path("data").mkdir(parents=True, exist_ok=True)

# SQLite engine — check_same_thread=False required for FastAPI's threading model
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Declarative base class shared by all ORM models."""
    pass


def init_db() -> None:
    """
    Create all database tables defined in ORM models.
    Must be called once at application startup.
    """
    # Import all models here so Base knows about them
    from backend.models import person  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("[green]✓[/green] Database tables initialized.")


def get_db():
    """
    FastAPI dependency that yields a database session.
    Ensures the session is always closed after the request.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
