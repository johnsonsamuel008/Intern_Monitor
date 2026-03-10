from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ---------------------------
# Persistent Device Entity
# ---------------------------
class DeviceBase(BaseModel):
    device_name: Optional[str] = None
    os_type: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    user_id: int 
    device_name: str
    os_type: str
    device_fingerprint: str 
    is_active: bool = True


class DeviceResponse(DeviceBase):
    id: int 
    user_id: Optional[int] 
    registered_at: datetime 
    last_seen: Optional[datetime]

    # Optional field used dynamically in dashboard logic
    is_online: Optional[bool] = False 


# ---------------------------
# Pairing / Device Authorization Schemas
# ---------------------------
class PairingCodeCreate(BaseModel):
    user_id: int 
    expires_in_minutes: int = 10


class PairingCodeResponse(BaseModel):
    pairing_token: str 
    id: int
    user_id: int


class DevicePairRequest(BaseModel):
    pairing_token: str 
    device_name: str
    os_type: str


class DevicePairResponse(BaseModel):
    status: str
    device_id: int
