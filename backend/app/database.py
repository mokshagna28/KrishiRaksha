"""
KRISHIRAKSHA AI - Database Engine & Session Factory
Supports PostgreSQL with seamless SQLite development fallback.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

logger = logging.getLogger("krishiraksha.database")

database_url = settings.DATABASE_URL

# Fallback mechanism: if postgres URL is specified but fails connection, fallback to SQLite
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    # Test connection
    with engine.connect() as conn:
        logger.info(f"Database connection successful with URL dialect: {engine.dialect.name}")
except Exception as e:
    logger.warning(f"Failed to connect to configured DATABASE_URL ({database_url}). Falling back to SQLite: {e}")
    database_url = "sqlite:///./krishiraksha.db"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
