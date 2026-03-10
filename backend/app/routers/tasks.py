import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import Task, User
from app.schemas.tasks import TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


def _serialize_task(task: Task) -> dict:
    return {
        "id": task.id,
        "assigned_to": task.assigned_to,
        "assigned_by": 0,
        "title": task.title,
        "description": task.description,
        "priority": None,
        "status": task.status,
        "due_date": None,
        "completion_percent": task.progress,
        "created_at": task.created_at,
    }


@router.get("/my-tasks", response_model=List[TaskResponse])
def get_my_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tasks = db.query(Task).filter(Task.assigned_to == user.id).all()
    return [_serialize_task(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_details(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if user.role != "admin" and task.assigned_to != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return _serialize_task(task)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task_progress(
    task_id: int,
    updates: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if user.role != "admin" and task.assigned_to != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = updates.model_dump(exclude_unset=True)
    valid_statuses = {"pending", "in_progress", "completed"}

    if "status" in update_data:
        new_status = update_data["status"]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid task status")
        task.status = new_status
        if new_status == "completed":
            task.completed_at = datetime.now(timezone.utc)
            task.progress = 100

    if "completion_percent" in update_data and update_data["completion_percent"] is not None:
        progress = int(update_data["completion_percent"])
        if progress < 0 or progress > 100:
            raise HTTPException(status_code=400, detail="completion_percent must be between 0 and 100")
        task.progress = progress
        if progress == 100 and task.status != "completed":
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Task update failed for task_id=%s", task_id)
        raise HTTPException(status_code=500, detail="Task update failed")
    db.refresh(task)
    return _serialize_task(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Task delete failed for task_id=%s", task_id)
        raise HTTPException(status_code=500, detail="Task delete failed")
    return None
