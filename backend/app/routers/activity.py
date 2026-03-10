import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_device
from app.models import ActivityLog, Device
from app.schemas.activity import IncomingLog

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])
logger = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED)
def ingest_logs(
    payloads: List[IncomingLog],
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
):
    if not payloads:
        raise HTTPException(status_code=400, detail="Empty payload batch")

    now = datetime.now(timezone.utc)
    new_logs = []

    for entry in payloads:
        data = entry.data
        is_flagged = False
        flag_reason = None

        if entry.type == "website" and data.get("url") and "blocked-site.com" in data.get("url", ""):
            is_flagged = True
            flag_reason = "Restricted URL Access"

        if data.get("cpu") is not None and data.get("cpu") > 90:
            is_flagged = True
            flag_reason = "High CPU usage detected"

        log = ActivityLog(
            device_id=device.id,
            user_id=device.user_id,
            activity_type=entry.type,
            recorded_at=entry.timestamp or now,
            activity_metadata=data,
            is_flagged=is_flagged,
            flag_reason=flag_reason,
            cpu_percent=data.get("cpu"),
            ram_percent=data.get("ram"),
        )
        new_logs.append(log)

    db.add_all(new_logs)
    device.last_seen = now

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Activity batch ingest failed for device_id=%s", device.id)
        raise HTTPException(status_code=500, detail="Failed to ingest logs")

    return {"status": "ok", "count": len(new_logs)}
