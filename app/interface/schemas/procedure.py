import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.domain.enums import LashTechnique


class ProcedureCreate(BaseModel):
    name: str
    technique: LashTechnique
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


class ProcedureUpdate(BaseModel):
    name: Optional[str] = None
    technique: Optional[LashTechnique] = None
    description: Optional[str] = None
    price_in_cents: Optional[int] = None
    duration_minutes: Optional[int] = None
    image_url: Optional[str] = None


class ProcedureResponse(BaseModel):
    id: uuid.UUID
    name: str
    technique: LashTechnique
    description: Optional[str]
    price_in_cents: int
    duration_minutes: int
    is_active: bool
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
