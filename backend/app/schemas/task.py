"""
app/schemas/task.py
~~~~~~~~~~~~~~~~~~~~
Pydantic schemas for task creation, responses, and status updates.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    description: str | None = None


class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None
    result: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskStatusUpdate(BaseModel):
    status: Literal["pending", "processing", "completed", "failed"]