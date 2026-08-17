"""
app/database/init_db.py
~~~~~~~~~~~~~~~~~~~~~~~~
Development-time helper to create database tables directly from
SQLAlchemy metadata.
"""

from app.database.connection import Base, engine
import app.models  # noqa: F401  (registers models with Base.metadata)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)