import uuid
from typing import Optional
from sqlmodel import SQLModel, Field


class BlockedDate(SQLModel, table=True):
    __tablename__ = "blocked_dates"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    date: str = Field(max_length=10, index=True)  # "YYYY-MM-DD"
    reason: Optional[str] = Field(default=None)
