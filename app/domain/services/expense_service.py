import uuid
from datetime import date
from dateutil.relativedelta import relativedelta
from app.domain.enums import ExpenseRecurrence
from typing import List

def _parse_reference_month(reference_month: str) -> date:
    """Parse 'YYYY-MM' string into a date object (day=1)."""
    year, month = map(int, reference_month.split("-"))
    return date(year, month, 1)


def _format_reference_month(d: date) -> str:
    return d.strftime("%Y-%m")


def generate_installments(
    name: str,
    category: str,
    amount_in_cents: int,
    due_day: int | None,
    reference_month: str,
    notes: str | None,
    installments: int,
) -> List[dict]:
    """
    Generates N installment dicts sharing the same installment_group_id.

    Each dict contains all fields needed to create an Expense record.
    recurrence is forced to 'monthly' for installment expenses.
    """
    group_id = uuid.uuid4()
    base_month = _parse_reference_month(reference_month)

    records = []
    for i in range(installments):
        month = _format_reference_month(base_month + relativedelta(months=i))
        records.append(
            {
                "name": name,
                "category": category,
                "amount_in_cents": amount_in_cents,
                "recurrence": ExpenseRecurrence.monthly,
                "due_day": due_day,
                "is_paid": False,
                "reference_month": month,
                "notes": notes,
                "installment_total": installments,
                "installment_current": i + 1,
                "installment_group_id": group_id,
            }
        )
    return records
