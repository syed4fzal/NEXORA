"""add task execution metadata

Revision ID: 0e4bd6a96460
Revises:
Create Date: 2026-08-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0e4bd6a96460"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add execution metadata columns to the existing tasks table."""

    op.add_column(
        "tasks",
        sa.Column(
            "execution_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "execution_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "execution_time",
            sa.Float(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove execution metadata columns from the tasks table."""

    op.drop_column("tasks", "execution_time")
    op.drop_column("tasks", "execution_completed_at")
    op.drop_column("tasks", "execution_started_at")