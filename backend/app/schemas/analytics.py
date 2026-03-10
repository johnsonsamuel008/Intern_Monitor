from pydantic import BaseModel
from typing import Optional

class AnalyticsSummaryResponse(BaseModel):
    online_interns_count: int
    total_logs_recorded: int
    high_bandwidth_alerts: int = 0  # SRS 3.4 requirement
    active_devices_count: int
    
    class Config:
        from_attributes = True
