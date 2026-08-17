"""
app/models
~~~~~~~~~~
SQLAlchemy ORM models. Importing this package registers every model with
Base.metadata, which Alembic relies on for schema generation.
"""

from app.models.user import User

__all__ = ["User"]