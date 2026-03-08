import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.domain.enums import MaterialCategory, MaterialUnit


class Material(SQLModel, table=True):
    __tablename__ = "materials"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    name: str = Field(max_length=200)
    category: MaterialCategory
    unit: MaterialUnit
    unit_cost_in_cents: int = Field(ge=0)
    current_stock: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
