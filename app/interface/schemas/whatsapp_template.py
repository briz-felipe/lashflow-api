import uuid
from datetime import datetime
from typing import Optional
from app.interface.schemas.base import CamelModel


class WhatsAppTemplateCreate(CamelModel):
    name: str
    description: Optional[str] = ""
    message: str


class WhatsAppTemplateUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    message: Optional[str] = None


class WhatsAppTemplateResponse(CamelModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str
    message: str
    created_at: datetime
    updated_at: datetime
