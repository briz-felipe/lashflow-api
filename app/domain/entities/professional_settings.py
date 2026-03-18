import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class ProfessionalSettings(SQLModel, table=True):
    __tablename__ = "professional_settings"

    professional_id: uuid.UUID = Field(primary_key=True)
    segment_rules: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
