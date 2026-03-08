import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from app.domain.enums import PaymentStatus, PaymentMethod


class PartialPaymentRecord(SQLModel, table=True):
    __tablename__ = "partial_payment_records"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    payment_id: uuid.UUID = Field(foreign_key="payments.id", index=True)
    amount_in_cents: int = Field(gt=0)
    method: PaymentMethod
    paid_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    appointment_id: uuid.UUID = Field(foreign_key="appointments.id", unique=True, index=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)

    total_amount_in_cents: int = Field(ge=0)
    paid_amount_in_cents: int = Field(default=0, ge=0)
    status: PaymentStatus = Field(default=PaymentStatus.pending)
    method: Optional[PaymentMethod] = Field(default=None)
    paid_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
