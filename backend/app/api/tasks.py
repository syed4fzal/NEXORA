"""
app/api/tasks.py
~~~~~~~~~~~~~~~~

Task routes for Nexora.

Provides endpoints to:
- create tasks
- list authenticated user's tasks
- retrieve a task
- update task status
- execute a task through the Nexora agent
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


tasks_router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


# ---------------------------------------------------------------------
# CREATE TASK
# ---------------------------------------------------------------------


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
    """Create a new task for the authenticated user."""

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


# ---------------------------------------------------------------------
# LIST TASKS
# ---------------------------------------------------------------------


@tasks_router.get(
    "",
    response_model=list[TaskResponse],
)
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Task]:
    """Return all tasks belonging to the authenticated user."""

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


# ---------------------------------------------------------------------
# GET TASK
# ---------------------------------------------------------------------


@tasks_router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    """Return a specific task owned by the authenticated user."""

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


# ---------------------------------------------------------------------
# UPDATE TASK STATUS
# ---------------------------------------------------------------------


@tasks_router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
)
def update_task_status(
    task_id: int,
    status_in: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    """Update the status of an authenticated user's task."""

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


# ---------------------------------------------------------------------
# RUN TASK
# ---------------------------------------------------------------------


@tasks_router.post(
    "/{task_id}/run",
    response_model=TaskResponse,
)
def run_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    """
    Execute a task through the complete Nexora agent pipeline.

    Flow:

        Task
          ↓
        NexoraAgent
          ↓
        Understanding
          ↓
        Decomposition
          ↓
        Planning
          ↓
        Tool Selection
          ↓
        Tool Execution
          ↓
        Verification
          ↓
        Final Report
          ↓
        Database
    """

    # -------------------------------------------------------------
    # Find task
    # -------------------------------------------------------------

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

    # -------------------------------------------------------------
    # Prevent unnecessary re-running
    # -------------------------------------------------------------

    if task.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already being processed",
        )

    # -------------------------------------------------------------
    # Mark task as processing
    # -------------------------------------------------------------

    task.status = "processing"

    db.commit()
    db.refresh(task)

    # -------------------------------------------------------------
    # Execute Nexora agent
    # -------------------------------------------------------------

    agent = NexoraAgent()

    task_text = task.description or task.title

    try:
        result = agent.process_task(task_text)

    except ValueError as exc:
        # Input/decomposition/planning errors.
        db.rollback()

        task.status = "failed"
        db.commit()
        db.refresh(task)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Unexpected agent/tool failure.
        db.rollback()

        task.status = "failed"
        db.commit()
        db.refresh(task)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task processing failed",
        ) from exc

    # -------------------------------------------------------------
    # Handle unsuccessful agent result
    # -------------------------------------------------------------

    if not result.success:
        task.status = "failed"

        # Keep useful information even when verification fails.
        task.result = (
            result.final_report
            or result.summary
        )

        db.commit()
        db.refresh(task)

        return task

    # -------------------------------------------------------------
    # Store successful final report
    # -------------------------------------------------------------

    task.result = (
        result.final_report
        or result.summary
    )

    task.status = "completed"

    db.commit()
    db.refresh(task)

    return task