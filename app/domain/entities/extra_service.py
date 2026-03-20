import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class ExtraService(SQLModel, table=True):
    """Catalog of additional charges/discounts a professional can apply to appointments."""
    __tablename__ = "extra_services"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    name: str = Field(max_length=200)                 # "Taxa de máquina", "Desconto VIP"
    description: Optional[str] = Field(default=None)
    default_amount_in_cents: int = Field(default=0, ge=0)  # 0 = manual entry each time
    # "add" = soma ao total  |  "deduct" = subtrai do total
    type: str = Field(default="add")
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
