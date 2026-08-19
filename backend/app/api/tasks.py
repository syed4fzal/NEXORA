"""
app/api/tasks.py

```
Task routes: create, list, retrieve, update the status of, and run the
authenticated user's tasks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.agent import NexoraAgent
from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskStatusUpdate

tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])


@tasks_router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = Task(
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        status="pending",
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@tasks_router.get("", response_model=list[TaskResponse])
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Task]:
    tasks = (
        db.execute(
            select(Task)
            .where(Task.user_id == current_user.id)
            .order_by(Task.created_at.desc())
        )
        .scalars()
        .all()
    )

    return list(tasks)


@tasks_router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@tasks_router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    status_in: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task.status = status_in.status

    db.commit()
    db.refresh(task)

    return task


@tasks_router.post("/{task_id}/run", response_model=TaskResponse)
def run_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Mark the task as processing.
    task.status = "processing"
    db.commit()
    db.refresh(task)

    agent = NexoraAgent()
    task_text = task.description or task.title

    try:
        # Run the complete Nexora agent pipeline.
        result = agent.process_task(task_text)

    except Exception:
        # If the agent fails, mark the task as failed.
        db.rollback()

        try:
            task.status = "failed"
            db.commit()
            db.refresh(task)
        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task processing failed",
        )

    # AgentResult is a Python object.
    # The PostgreSQL result column expects a string.
    # Therefore, store only the final summary.
    task.result = result.summary
    task.status = "completed"

    db.commit()
    db.refresh(task)

    return task

