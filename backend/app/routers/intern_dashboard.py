from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Device, Task, User

router = APIRouter(prefix="/intern/dashboard", tags=["Intern Dashboard"])


@router.get("/my-tasks")
def get_my_tasks(
    current_user: User = Depends(require_roles("intern")),
    db: Session = Depends(get_db),
):
    """Allows interns to see only their assigned work (SRS 3.1)."""
    return db.query(Task).filter(Task.assigned_to == current_user.id).all()


@router.get("/my-devices")
def get_my_devices(
    current_user: User = Depends(require_roles("intern")),
    db: Session = Depends(get_db),
):
    """Check status of their own registered devices (SRS 5.0)."""
    return db.query(Device).filter(Device.user_id == current_user.id).all()
