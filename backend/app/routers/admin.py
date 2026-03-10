import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import ActivityLog, Device, Task, User
from app.schemas.activity import ActivityLogResponse
from app.schemas.analytics import AnalyticsSummaryResponse
from app.schemas.devices import DeviceResponse, PairingCodeResponse
from app.schemas.tasks import TaskCreate, TaskResponse
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/admin", tags=["Admin / Supervisor Dashboard"])
logger = logging.getLogger(__name__)


def _rollback_and_raise_500(db: Session, detail: str) -> None:
    db.rollback()
    raise HTTPException(status_code=500, detail=detail)


def _serialize_activity_log(log: ActivityLog) -> dict:
    """
    Bridge canonical DB fields to legacy API response fields without schema churn.
    """
    return {
        "id": log.id,
        "device_id": log.device_id,
        "intern_name": log.user.username if log.user else "unknown",
        "activity_type": log.activity_type,
        "metadata": log.activity_metadata or {},
        "timestamp": log.recorded_at,
        "is_flagged": log.is_flagged,
        "flag_reason": log.flag_reason,
    }


def _serialize_task(task: Task, assigned_by: int = 0) -> dict:
    """
    Keep response compatibility with current TaskResponse schema while persisting
    only canonical model columns.
    """
    return {
        "id": task.id,
        "assigned_to": task.assigned_to,
        "assigned_by": assigned_by,
        "title": task.title,
        "description": task.description,
        "priority": None,
        "status": task.status,
        "due_date": None,
        "completion_percent": task.progress,
        "created_at": task.created_at,
    }


# =============================
# 1. USER MANAGEMENT (SRS 3.1)
# =============================


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Create an intern or admin account (SRS 7.1)."""
    username = data.username.strip()
    email = data.email.strip().lower()

    if db.query(User.id).filter((User.username == username) | (User.email == email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        logger.warning("User create conflict for username=%s email=%s", username, email)
        _rollback_and_raise_500(db, "User create failed due to conflicting data")
    except Exception:
        logger.exception("User create failed")
        _rollback_and_raise_500(db, "User create failed")
    db.refresh(user)
    return user


@router.get("/users", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = Query(default=None, pattern="^(admin|intern)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    """List all users (interns/admins) and their status."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.id.desc()).offset(offset).limit(limit).all()


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Update user details dynamically (Full CRUD)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)

    # Explicit allow-list avoids accidental writes to sensitive/unexpected attrs.
    if "username" in update_data:
        user.username = update_data["username"].strip()
    if "email" in update_data:
        user.email = update_data["email"].strip().lower()
    if "role" in update_data:
        user.role = update_data["role"]
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]
    if "password" in update_data and update_data["password"]:
        user.password_hash = hash_password(update_data["password"])

    try:
        db.commit()
    except IntegrityError:
        logger.warning("User update conflict for user_id=%s", user_id)
        _rollback_and_raise_500(db, "User update failed due to conflicting data")
    except Exception:
        logger.exception("User update failed for user_id=%s", user_id)
        _rollback_and_raise_500(db, "User update failed")
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Delete a user and cascade data (SRS 5)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    try:
        db.commit()
    except Exception:
        logger.exception("User delete failed for user_id=%s", user_id)
        _rollback_and_raise_500(db, "User delete failed")


# =============================
# 2. DEVICE MANAGEMENT (SRS 5)
# =============================


@router.post("/devices/pairing-token", response_model=PairingCodeResponse)
def create_pairing_token(intern_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Generate a one-time token for an intern (SRS 7.2)."""
    target_user = db.query(User).filter(User.id == intern_id, User.role == "intern").first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Intern not found")

    token = secrets.token_urlsafe(32)
    device = Device(user_id=intern_id, pairing_token=token, is_active=True)
    db.add(device)
    try:
        db.commit()
    except IntegrityError:
        # Extremely unlikely token collision; preserves safety under concurrency.
        logger.warning("Pairing token collision for intern_id=%s", intern_id)
        _rollback_and_raise_500(db, "Pairing token generation failed, retry")
    except Exception:
        logger.exception("Pairing token creation failed for intern_id=%s", intern_id)
        _rollback_and_raise_500(db, "Pairing token generation failed")
    db.refresh(device)
    return device


@router.get("/devices", response_model=List[DeviceResponse])
def list_devices(
    user_id: Optional[int] = Query(default=None, ge=1),
    is_active: Optional[bool] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    """List all registered and pending devices (Full Device CRUD)."""
    query = db.query(Device)
    if user_id is not None:
        query = query.filter(Device.user_id == user_id)
    if is_active is not None:
        query = query.filter(Device.is_active.is_(is_active))
    return query.order_by(Device.id.desc()).offset(offset).limit(limit).all()


@router.patch("/devices/{device_id}/status")
def set_device_status(device_id: int, is_active: bool = Query(...), db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Activate/Deactivate a device (e.g., if stolen) (SRS 5.2)."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_active = is_active
    try:
        db.commit()
    except Exception:
        logger.exception("Device status update failed for device_id=%s", device_id)
        _rollback_and_raise_500(db, "Device status update failed")
    return {"status": "success", "message": f"Device activity set to {is_active}"}


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Hard delete a device registration (SRS 5.3)."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
    try:
        db.commit()
    except Exception:
        logger.exception("Device delete failed for device_id=%s", device_id)
        _rollback_and_raise_500(db, "Device delete failed")


# =============================
# 3. MONITORING (SRS 3.2, 3.4)
# =============================


@router.get("/logs/all", response_model=List[ActivityLogResponse])
def get_all_activity_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    """Latest activity across the organization (SRS 3.2)."""
    logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.recorded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_serialize_activity_log(log) for log in logs]


@router.get("/logs/flagged", response_model=List[ActivityLogResponse])
def get_flagged_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    """View suspicious or high-bandwidth activity (SRS 3.4)."""
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.is_flagged.is_(True))
        .order_by(ActivityLog.recorded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_serialize_activity_log(log) for log in logs]


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Aggregate data for the main dashboard metrics (SRS 3.4)."""
    online_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)

    online_count = (
        db.query(func.count(func.distinct(Device.user_id)))
        .join(User, User.id == Device.user_id)
        .filter(
            User.role == "intern",
            Device.is_active.is_(True),
            Device.last_seen >= online_threshold,
        )
        .scalar()
    ) or 0

    log_counts = db.query(
        func.count(ActivityLog.id).label("total_logs_recorded"),
        func.sum(
            case(
                (ActivityLog.is_flagged.is_(True), 1),
                else_=0,
            )
        ).label("high_bandwidth_alerts"),
    ).one()

    return {
        "online_interns_count": int(online_count),
        "total_logs_recorded": int(log_counts.total_logs_recorded or 0),
        "active_devices_count": db.query(Device).filter(Device.is_active.is_(True)).count(),
        "high_bandwidth_alerts": int(log_counts.high_bandwidth_alerts or 0),
    }


# =============================
# 4. TASK MANAGEMENT (SRS 3.1)
# =============================


@router.post("/tasks", response_model=TaskResponse)
def assign_task(data: TaskCreate, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    """Assign a new task to an intern (SRS 3.1)."""
    assignee = db.query(User.id).filter(User.id == data.assigned_to, User.role == "intern").first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assigned intern not found")

    task = Task(
        assigned_to=data.assigned_to,
        title=data.title,
        description=data.description,
        status="pending",
        progress=0,
    )
    db.add(task)
    try:
        db.commit()
    except Exception:
        logger.exception("Task create failed assigned_to=%s", data.assigned_to)
        _rollback_and_raise_500(db, "Task assignment failed")
    db.refresh(task)
    return _serialize_task(task, assigned_by=admin.id)


@router.get("/tasks", response_model=List[TaskResponse])
def list_all_tasks(
    assigned_to: Optional[int] = Query(default=None, ge=1),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    """View status of all assigned tasks."""
    query = db.query(Task)
    if assigned_to is not None:
        query = query.filter(Task.assigned_to == assigned_to)
    if status_filter:
        query = query.filter(Task.status == status_filter)

    tasks = query.order_by(Task.id.desc()).offset(offset).limit(limit).all()
    return [_serialize_task(task) for task in tasks]
