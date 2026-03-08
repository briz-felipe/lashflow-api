import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.domain.enums import MaterialCategory, MaterialUnit


class MaterialCreate(BaseModel):
    name: str
    category: MaterialCategory
    unit: MaterialUnit
    unit_cost_in_cents: int
    current_stock: int = 0
    minimum_stock: int = 0
    notes: Optional[str] = None


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[MaterialCategory] = None
    unit: Optional[MaterialUnit] = None
    unit_cost_in_cents: Optional[int] = None
    minimum_stock: Optional[int] = None
    notes: Optional[str] = None


class MaterialResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: MaterialCategory
    unit: MaterialUnit
    unit_cost_in_cents: int
    current_stock: int
    minimum_stock: int
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StockValueResponse(BaseModel):
    total_value_in_cents: int
