import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from app.domain.enums import StockMovementType


class StockMovement(SQLModel, table=True):
    __tablename__ = "stock_movements"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    material_id: uuid.UUID = Field(foreign_key="materials.id", index=True)

    type: StockMovementType
    quantity: int = Field(gt=0)
    unit_cost_in_cents: int = Field(ge=0)
    total_cost_in_cents: int = Field(ge=0)  # calculated: quantity * unit_cost_in_cents
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    notes: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
