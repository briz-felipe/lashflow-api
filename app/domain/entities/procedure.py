import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.domain.enums import LashTechnique


class Procedure(SQLModel, table=True):
    __tablename__ = "procedures"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    name: str = Field(max_length=200)
    technique: LashTechnique
    description: Optional[str] = Field(default=None)
    price_in_cents: int = Field(gt=0)
    duration_minutes: int = Field(gt=0)
    is_active: bool = Field(default=True)
    image_url: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
