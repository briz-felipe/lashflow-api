import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.domain.enums import StockMovementType


class StockMovementCreate(BaseModel):
    material_id: uuid.UUID
    type: StockMovementType
    quantity: int
    unit_cost_in_cents: int
    notes: Optional[str] = None


class StockMovementResponse(BaseModel):
    id: uuid.UUID
    material_id: uuid.UUID
    type: StockMovementType
    quantity: int
    unit_cost_in_cents: int
    total_cost_in_cents: int
    date: datetime
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
