import uuid
import re
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug.strip("_")[:100]


class WhatsAppTemplate(SQLModel, table=True):
    __tablename__ = "whatsapp_templates"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    slug: str = Field(max_length=100)          # auto-generated from name, unique per professional
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=500)
    message: str = Field(max_length=2000)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
