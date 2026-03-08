import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.domain.enums import ExpenseRecurrence


class Expense(SQLModel, table=True):
    __tablename__ = "expenses"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    name: str = Field(max_length=200)
    category: str = Field(max_length=100)  # free string, not enum
    amount_in_cents: int = Field(ge=0)
    recurrence: ExpenseRecurrence
    due_day: Optional[int] = Field(default=None, ge=1, le=31)
    is_paid: bool = Field(default=False)
    paid_at: Optional[datetime] = Field(default=None)
    reference_month: str = Field(index=True, max_length=7)  # "YYYY-MM"
    notes: Optional[str] = Field(default=None)

    # Installment fields
    installment_total: Optional[int] = Field(default=None, gt=0)
    installment_current: Optional[int] = Field(default=None, gt=0)
    installment_group_id: Optional[uuid.UUID] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
