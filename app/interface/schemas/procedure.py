import uuid
from datetime import datetime
from typing import Optional
from pydantic import field_validator
from app.interface.schemas.base import CamelModel


class ProcedureCreate(CamelModel):
    name: str
    description: Optional[str] = None
    price_in_cents: int
    duration_minutes: int
    image_url: Optional[str] = None

    @field_validator("price_in_cents")
    @classmethod
    def price_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("price_in_cents must be > 0")
        return v

    @field_validator("duration_minutes")
    @classmethod
    def duration_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("duration_minutes must be > 0")
        return v


class ProcedureUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_in_cents: Optional[int] = None
    duration_minutes: Optional[int] = None
    image_url: Optional[str] = None


class ProcedureResponse(CamelModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    price_in_cents: int
    duration_minutes: int
    is_active: bool
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
