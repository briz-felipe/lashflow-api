import uuid
from datetime import datetime
from typing import Optional
from app.interface.schemas.base import CamelModel


class LoginRequest(CamelModel):
    username: str
    password: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class RegisterRequest(CamelModel):
    username: str
    password: str
    email: Optional[str] = None


class TokenResponse(CamelModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(CamelModel):
    refresh_token: str


class TokenValidateResponse(CamelModel):
    valid: bool
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    expires_at: Optional[datetime] = None


class MeResponse(CamelModel):
    id: uuid.UUID
    username: str
    email: Optional[str]
    is_superuser: bool
    is_active: bool
    created_at: datetime
