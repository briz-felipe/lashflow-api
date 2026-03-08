import uuid
from typing import Optional
from pydantic import BaseModel


class BlockedDateCreate(BaseModel):
    date: str  # "YYYY-MM-DD"
    reason: Optional[str] = None


class BlockedDateResponse(BaseModel):
    id: uuid.UUID
    date: str
    reason: Optional[str]

    model_config = {"from_attributes": True}
