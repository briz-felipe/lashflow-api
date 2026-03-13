import uuid
from typing import Optional
from app.interface.schemas.base import CamelModel


class BlockedDateCreate(CamelModel):
    date: str  # "YYYY-MM-DD"
    reason: Optional[str] = None


class BlockedDateResponse(CamelModel):
    id: uuid.UUID
    date: str
    reason: Optional[str]
