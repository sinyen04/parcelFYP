"""
SQLAlchemy database setup.

Uses SQLite for local development. To switch to PostgreSQL,
simply change DATABASE_URL in .env to a PostgreSQL connection string, e.g.:
  DATABASE_URL=postgresql://user:password@localhost:5432/parcel_db
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# For SQLite, need check_same_thread=False to allow FastAPI's async usage
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
