"""Database configuration and session management."""

import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/authapp")

# Optimized connection pool settings for better performance
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Max additional connections beyond pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Timeout for getting connection from pool
    echo=False,  # Set to True for SQL debugging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
