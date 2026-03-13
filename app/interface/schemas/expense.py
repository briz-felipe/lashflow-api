import uuid
from datetime import datetime
from typing import Optional
from app.domain.enums import ExpenseRecurrence
from app.interface.schemas.base import CamelModel


class ExpenseCreate(CamelModel):
    name: str
    category: str
    amount_in_cents: int
    recurrence: ExpenseRecurrence
    due_day: Optional[int] = None
    reference_month: str  # "YYYY-MM"
    notes: Optional[str] = None
    installments: Optional[int] = None  # > 1 triggers installment generation


class ExpenseUpdate(CamelModel):
    name: Optional[str] = None
    category: Optional[str] = None
    amount_in_cents: Optional[int] = None
    recurrence: Optional[ExpenseRecurrence] = None
    due_day: Optional[int] = None
    reference_month: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(CamelModel):
    id: uuid.UUID
    name: str
    category: str
    amount_in_cents: int
    recurrence: ExpenseRecurrence
    due_day: Optional[int]
    is_paid: bool
    paid_at: Optional[datetime]
    reference_month: str
    notes: Optional[str]
    installment_total: Optional[int]
    installment_current: Optional[int]
    installment_group_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class ExpenseInstallmentResponse(CamelModel):
    expense: ExpenseResponse
    installments_created: int
    installment_group_id: Optional[uuid.UUID] = None


class ExpenseSummaryResponse(CamelModel):
    month: str
    total_in_cents: int
    paid_in_cents: int
    pending_in_cents: int
    by_category: dict[str, int]
