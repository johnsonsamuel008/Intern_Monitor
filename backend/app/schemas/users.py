from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Literal
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: Literal["admin", "intern"]
    is_active: bool = True

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Literal["admin", "intern"]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None  # Allow password updates if needed

# Schema for /auth/login request
class LoginRequest(BaseModel):
    username: str
    password: str

# Schema for Token responses
class Token(BaseModel):
    access_token: str
    token_type: str

# Properties to return via API
class UserResponse(UserBase):
    id: int
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    # Pydantic V2 configuration to support SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)
