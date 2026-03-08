import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.domain.enums import PaymentStatus, PaymentMethod


class PartialPaymentRequest(BaseModel):
    amount_in_cents: int
    method: PaymentMethod


class PartialPaymentRecordResponse(BaseModel):
    id: uuid.UUID
    amount_in_cents: int
    method: PaymentMethod
    paid_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    appointment_id: uuid.UUID
    client_id: uuid.UUID
    total_amount_in_cents: int
    paid_amount_in_cents: int = 0
    method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    partial_payment: Optional[PartialPaymentRequest] = None
    paid_amount_in_cents: Optional[int] = None
    method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    client_id: uuid.UUID
    total_amount_in_cents: int
    paid_amount_in_cents: int
    status: PaymentStatus
    method: Optional[PaymentMethod]
    paid_at: Optional[datetime]
    notes: Optional[str]
    partial_payments: List[PartialPaymentRecordResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentStatsResponse(BaseModel):
    today_in_cents: int
    this_week_in_cents: int
    this_month_in_cents: int
    last_month_in_cents: int
    growth_percent: float


class MonthlyRevenueItem(BaseModel):
    month: str
    amount_in_cents: int


class MethodBreakdownResponse(BaseModel):
    cash: int = 0
    credit_card: int = 0
    debit_card: int = 0
    pix: int = 0
    bank_transfer: int = 0
    other: int = 0
