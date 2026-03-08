import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class Client(SQLModel, table=True):
    __tablename__ = "clients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    name: str = Field(max_length=200)
    phone: str = Field(max_length=20, index=True)  # digits only
    email: Optional[str] = Field(default=None)
    instagram: Optional[str] = Field(default=None, max_length=100)
    birthday: Optional[str] = Field(default=None)  # "YYYY-MM-DD"
    notes: Optional[str] = Field(default=None)

    # JSON fields
    address: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    segments: list = Field(default_factory=list, sa_column=Column(JSON))

    favorite_procedure_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="procedures.id"
    )

    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
