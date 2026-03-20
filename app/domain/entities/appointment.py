import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from app.domain.enums import AppointmentStatus, LashServiceType, CancelledBy


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    procedure_id: uuid.UUID = Field(foreign_key="procedures.id", index=True)
    payment_id: Optional[uuid.UUID] = Field(default=None, foreign_key="payments.id")

    service_type: Optional[LashServiceType] = Field(default=None)
    status: AppointmentStatus = Field(default=AppointmentStatus.pending_approval, index=True)

    scheduled_at: datetime = Field(index=True)
    duration_minutes: int = Field(gt=0)
    price_charged: int = Field(ge=0)

    notes: Optional[str] = Field(default=None)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    cancellation_reason: Optional[str] = Field(default=None)
    cancelled_by: Optional[CancelledBy] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Override for combined multi-procedure names (e.g. "Remoção + Volume Russo")
    procedure_name_override: Optional[str] = Field(default=None)

    # Apple Calendar sync
    apple_event_uid: Optional[str] = Field(default=None, max_length=100)

    @property
    def ends_at(self) -> datetime:
        return self.scheduled_at + timedelta(minutes=self.duration_minutes)
