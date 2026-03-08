import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenValidateResponse(BaseModel):
    valid: bool
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    expires_at: Optional[datetime] = None


class MeResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: Optional[str]
    is_superuser: bool
    is_active: bool
    created_at: datetime
