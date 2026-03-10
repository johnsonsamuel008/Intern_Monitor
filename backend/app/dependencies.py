from datetime import datetime, timezone
from typing import List

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decode_access_token
from app.models import User, Device

security = HTTPBearer()

# =========================
# USER AUTH (JWT)
# =========================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        
        if not user_id_raw:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject",
            )
        
        # Standard Integer ID conversion
        user_id = int(user_id_raw)
            
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User ID format in token",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
        )
        
    return user

# Consolidated Role Checker
class require_roles:
    def __init__(self, *allowed_roles: str):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {self.allowed_roles}",
            )
        return current_user

# =========================
# DEVICE AUTH
# =========================

def get_current_device(
    authorization: str = Header(..., description="Authorization: Device <pairing_token>"),
    db: Session = Depends(get_db),
) -> Device:
    """
    Standard device lookup. 
    Matches the pairing_token provided by the hardware client.
    """
    if not authorization.startswith("Device "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header must start with 'Device '",
        )

    token = authorization.replace("Device ", "", 1).strip()
    
    # Standard Integer-based ID systems still use string tokens for auth
    device = db.query(Device).filter(
        Device.pairing_token == token, 
        Device.is_active.is_(True)
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Device not recognized or requires re-pairing"
        )

    # Standard "Last Seen" heartbeat
    device.last_seen = datetime.now(timezone.utc)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device heartbeat"
        )
        
    return device
