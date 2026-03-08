from app.domain.enums import PaymentStatus
from typing import List

def calculate_payment_status(paid_amount: int, total_amount: int) -> PaymentStatus:
    """
    Determines PaymentStatus based on paid vs total amounts.
    - 0 paid         → pending
    - partial paid   → partial
    - fully paid     → paid
    """
    if paid_amount <= 0:
        return PaymentStatus.pending
    if paid_amount < total_amount:
        return PaymentStatus.partial
    return PaymentStatus.paid


def sum_partial_payments(partial_amounts: List[int]) -> int:
    """Returns the sum of all partial payment amounts in cents."""
    return sum(partial_amounts)
