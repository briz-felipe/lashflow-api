import uuid
from datetime import datetime
from typing import Optional
from app.domain.enums import MaterialUnit
from app.interface.schemas.base import CamelModel


class MaterialCreate(CamelModel):
    name: str
    category: str
    unit: MaterialUnit
    unit_cost_in_cents: int
    current_stock: int = 0
    minimum_stock: int = 0
    notes: Optional[str] = None


class MaterialUpdate(CamelModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[MaterialUnit] = None
    unit_cost_in_cents: Optional[int] = None
    minimum_stock: Optional[int] = None
    notes: Optional[str] = None


class MaterialResponse(CamelModel):
    id: uuid.UUID
    name: str
    category: str
    unit: MaterialUnit
    unit_cost_in_cents: int
    current_stock: int
    minimum_stock: int
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class StockValueResponse(CamelModel):
    total_value_in_cents: int
