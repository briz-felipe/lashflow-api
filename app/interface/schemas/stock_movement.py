import uuid
from datetime import datetime
from typing import Optional
from app.domain.enums import StockMovementType
from app.interface.schemas.base import CamelModel


class StockMovementCreate(CamelModel):
    material_id: uuid.UUID
    type: StockMovementType
    quantity: int
    unit_cost_in_cents: int
    expense_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class StockMovementUpdate(CamelModel):
    quantity: Optional[int] = None
    unit_cost_in_cents: Optional[int] = None
    expense_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class StockMovementResponse(CamelModel):
    id: uuid.UUID
    material_id: uuid.UUID
    material_name: Optional[str] = None
    type: StockMovementType
    quantity: int
    unit_cost_in_cents: int
    total_cost_in_cents: int
    expense_id: Optional[uuid.UUID] = None
    date: datetime
    notes: Optional[str]
    created_at: datetime
