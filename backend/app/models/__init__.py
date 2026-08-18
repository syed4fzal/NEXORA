"""
app/models
~~~~~~~~~~
SQLAlchemy ORM models. Importing this package registers every model with
Base.metadata, which Alembic and init_db rely on for schema generation.
"""

from app.models.user import User
from app.models.task import Task

__all__ = ["User", "Task"]