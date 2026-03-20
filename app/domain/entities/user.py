import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=100)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    password_hash: str
    is_superuser: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Salon profile (white-label)
    salon_name: Optional[str] = Field(default=None, max_length=100)
    salon_slug: Optional[str] = Field(default=None, max_length=50, index=True)
    salon_address: Optional[str] = Field(default=None, max_length=300)

    # LashFlow cycle settings
    maintenance_cycle_days: int = Field(default=15)

    # Apple Calendar integration
    apple_id: Optional[str] = Field(default=None, max_length=200)
    apple_password_encrypted: Optional[str] = Field(default=None)
    apple_calendar_name: Optional[str] = Field(default=None, max_length=200)
