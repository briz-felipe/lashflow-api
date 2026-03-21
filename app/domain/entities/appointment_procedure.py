import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class AppointmentProcedure(SQLModel, table=True):
    __tablename__ = "appointment_procedures"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    appointment_id: uuid.UUID = Field(foreign_key="appointments.id", index=True)
    procedure_id: uuid.UUID = Field(foreign_key="procedures.id", index=True)

    custom_price_in_cents: Optional[int] = Field(default=None)
    original_price_in_cents: int = Field(ge=0)
    duration_minutes: int = Field(gt=0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def effective_price(self) -> int:
        if self.custom_price_in_cents is not None:
            return self.custom_price_in_cents
        return self.original_price_in_cents
