"""
app/models/task.py
~~~~~~~~~~~~~~~~~~~

Task model for Nexora.

A task belongs to a user and stores:
- task information
- execution status
- execution result
- execution timing
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Task(Base):
    """A unit of work a user asks Nexora to automate."""

    __tablename__ = "tasks"

    # -------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    # -------------------------------------------------------------
    # Task information
    # -------------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # -------------------------------------------------------------
    # Execution result
    # -------------------------------------------------------------

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    # -------------------------------------------------------------
    # Execution timing
    # -------------------------------------------------------------

    execution_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    execution_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    execution_time: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    # -------------------------------------------------------------
    # Record timestamps
    # -------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Task "
            f"id={self.id} "
            f"user_id={self.user_id} "
            f"title={self.title!r} "
            f"status={self.status!r}>"
        )