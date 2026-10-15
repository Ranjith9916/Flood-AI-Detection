"""
backend/app/core/database.py
SQLAlchemy database engine and session factory.
Reads DATABASE_URL from config (environment variables).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.app.core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=settings.db_pool_pre_ping,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session.
    Automatically closes the session after the request.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
