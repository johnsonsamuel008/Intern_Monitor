from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    status: str = "pending"
    due_date: Optional[date] = None
    completion_percent: int = 0
    
class TaskCreate(TaskBase):
    assigned_to: int 
    
class TaskUpdate(BaseModel):
    status: Optional[str] = None
    completion_percent: Optional[int] = None
    
class TaskResponse(TaskBase):
    id: int 
    assigned_to: int 
    assigned_by: int 
    created_at: datetime
    
    class Config:
        from_attributes = True
