import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import select, func

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.expense import Expense
from typing import List

class ExpenseRepository(BaseRepository[Expense]):
    def _base_query(self, professional_id: uuid.UUID):
        return select(Expense).where(Expense.professional_id == professional_id)

    def list(
        self,
        professional_id: uuid.UUID,
        month: Optional[str] = None,
        category: Optional[str] = None,
        is_paid: Optional[bool] = None,
    ) -> List[Expense]:
        stmt = self._base_query(professional_id)
        if month:
            stmt = stmt.where(Expense.reference_month == month)
        if category:
            stmt = stmt.where(Expense.category == category)
        if is_paid is not None:
            stmt = stmt.where(Expense.is_paid == is_paid)
        return list(self.session.exec(stmt.order_by(Expense.created_at.desc())).all())

    def get_by_id(self, professional_id: uuid.UUID, expense_id: uuid.UUID) -> Optional[Expense]:
        return self.session.exec(
            self._base_query(professional_id).where(Expense.id == expense_id)
        ).first()

    def create(self, expense: Expense) -> Expense:
        return self._save(expense)

    def create_many(self, expenses: List[Expense]) -> List[Expense]:
        for e in expenses:
            self.session.add(e)
        self.session.commit()
        for e in expenses:
            self.session.refresh(e)
        return expenses

    def update(self, expense: Expense) -> Expense:
        return self._touch(expense)

    def delete(self, expense: Expense) -> None:
        self._delete(expense)

    def mark_paid(self, expense: Expense) -> Expense:
        expense.is_paid = True
        expense.paid_at = datetime.utcnow()
        return self._touch(expense)

    def get_summary(self, professional_id: uuid.UUID, month: str) -> dict:
        expenses = self.list(professional_id, month=month)
        total = sum(e.amount_in_cents for e in expenses)
        paid = sum(e.amount_in_cents for e in expenses if e.is_paid)
        pending = total - paid

        by_category: dict[str, int] = {}
        for e in expenses:
            by_category[e.category] = by_category.get(e.category, 0) + e.amount_in_cents

        return {
            "month": month,
            "total_in_cents": total,
            "paid_in_cents": paid,
            "pending_in_cents": pending,
            "by_category": by_category,
        }

    def get_monthly_totals(self, professional_id: uuid.UUID, months: int = 6) -> List[dict]:
        from datetime import datetime as dt_cls, timezone
        now = dt_cls.now(timezone.utc)
        results = []
        for i in range(months - 1, -1, -1):
            if now.month - i <= 0:
                year = now.year - 1
                month = 12 + (now.month - i)
            else:
                year = now.year
                month = now.month - i
            month_str = f"{year:04d}-{month:02d}"
            total = self.session.exec(
                select(func.coalesce(func.sum(Expense.amount_in_cents), 0)).where(
                    Expense.professional_id == professional_id,
                    Expense.reference_month == month_str,
                )
            ).one() or 0
            results.append({"month": month_str, "total_in_cents": total})
        return results
