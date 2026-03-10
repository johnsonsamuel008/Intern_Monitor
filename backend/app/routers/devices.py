import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_device
from app.models import Device
from app.schemas.devices import DevicePairRequest, DevicePairResponse

router = APIRouter(prefix="/devices", tags=["Devices"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=DevicePairResponse)
def register_device(
    data: DevicePairRequest,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
):
    """
    Finalizes device registration using the token from Authorization header.
    """
    if data.pairing_token != device.pairing_token:
        raise HTTPException(status_code=400, detail="Pairing token mismatch")

    device.device_name = data.device_name
    device.os_type = data.os_type
    device.is_active = True

    # Keep pairing_token available because current log-ingestion auth depends on it.
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Device registration failed for device_id=%s", device.id)
        raise HTTPException(status_code=500, detail="Device registration failed")
    db.refresh(device)

    return {
        "status": "registered",
        "device_id": device.id,
    }
