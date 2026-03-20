import uuid
from datetime import datetime
from typing import Optional, List
from app.domain.enums import PaymentStatus, PaymentMethod
from app.interface.schemas.base import CamelModel


class PartialPaymentRequest(CamelModel):
    amount_in_cents: int
    method: PaymentMethod


class PartialPaymentRecordResponse(CamelModel):
    id: uuid.UUID
    amount_in_cents: int
    method: PaymentMethod
    paid_at: datetime


class PaymentCreate(CamelModel):
    appointment_id: uuid.UUID
    client_id: uuid.UUID
    subtotal_amount_in_cents: int = 0
    discount_amount_in_cents: int = 0
    fee_amount_in_cents: int = 0
    total_amount_in_cents: int
    paid_amount_in_cents: int = 0
    method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class PaymentUpdate(CamelModel):
    partial_payment: Optional[PartialPaymentRequest] = None
    subtotal_amount_in_cents: Optional[int] = None
    discount_amount_in_cents: Optional[int] = None
    fee_amount_in_cents: Optional[int] = None
    paid_amount_in_cents: Optional[int] = None
    method: Optional[PaymentMethod] = None
    notes: Optional[str] = None
    status: Optional[PaymentStatus] = None
    paid_at: Optional[datetime] = None


class PaymentResponse(CamelModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    client_id: uuid.UUID
    subtotal_amount_in_cents: int
    discount_amount_in_cents: int
    fee_amount_in_cents: int
    total_amount_in_cents: int
    paid_amount_in_cents: int
    status: PaymentStatus
    method: Optional[PaymentMethod]
    paid_at: Optional[datetime]
    notes: Optional[str]
    partial_payments: List[PartialPaymentRecordResponse] = []
    created_at: datetime
    updated_at: datetime


class CashFlowItemResponse(CamelModel):
    id: uuid.UUID
    appointment_id: Optional[uuid.UUID]
    client_id: uuid.UUID
    client_name: Optional[str] = None
    procedure_name: Optional[str] = None
    total_amount_in_cents: int
    paid_amount_in_cents: int
    method: Optional[PaymentMethod]
    status: PaymentStatus
    created_at: datetime


class PaymentStatsResponse(CamelModel):
    today_in_cents: int
    this_week_in_cents: int
    this_month_in_cents: int
    last_month_in_cents: int
    growth_percent: float


class MonthlyRevenueItem(CamelModel):
    month: str
    amount_in_cents: int


class MethodBreakdownResponse(CamelModel):
    cash: int = 0
    credit_card: int = 0
    debit_card: int = 0
    pix: int = 0
    bank_transfer: int = 0
    other: int = 0
