from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Dict, Optional, Literal

class IncomingLog(BaseModel):
    # 'type' maps to activity_type in DB
    type: Literal["application", "website", "system", "resource", "idle"]
    # 'data' maps to raw_payload/metadata
    data: Dict 
    timestamp: Optional[datetime] = None

    class Config:
        # Standardizes time to UTC if not provided
        json_encoders = {datetime: lambda v: v.now(timezone.utc)}

class ActivityLogResponse(BaseModel):
    id: int
    device_id: int
    intern_name: str  # Joined from User model
    activity_type: str 
    metadata: Dict     # The 'data' from IncomingLog
    timestamp: datetime
    is_flagged: bool   # Critical for SRS 3.4
    flag_reason: Optional[str] = None

    class Config:
        from_attributes = True
