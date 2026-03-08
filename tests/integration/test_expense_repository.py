import uuid
from app.infrastructure.repositories.expense_repository import ExpenseRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.entities.expense import Expense
from app.domain.entities.user import User
from app.domain.enums import ExpenseRecurrence
from app.domain.services.expense_service import generate_installments
from app.interface.dependencies import hash_password


def _make_professional(session) -> User:
    repo = UserRepository(session)
    return repo.create(User(
        username="prof",
        email="prof@test.com",
        password_hash=hash_password("pass"),
        is_superuser=True,
    ))


class TestExpenseRepository:
    def test_create_and_get(self, session):
        prof = _make_professional(session)
        repo = ExpenseRepository(session)
        expense = repo.create(Expense(
            professional_id=prof.id,
            name="Aluguel",
            category="aluguel",
            amount_in_cents=150000,
            recurrence=ExpenseRecurrence.monthly,
            reference_month="2024-03",
        ))
        found = repo.get_by_id(prof.id, expense.id)
        assert found is not None
        assert found.name == "Aluguel"

    def test_mark_paid(self, session):
        prof = _make_professional(session)
        repo = ExpenseRepository(session)
        expense = repo.create(Expense(
            professional_id=prof.id,
            name="Internet",
            category="internet",
            amount_in_cents=10000,
            recurrence=ExpenseRecurrence.monthly,
            reference_month="2024-03",
        ))
        assert expense.is_paid is False
        paid = repo.mark_paid(expense)
        assert paid.is_paid is True
        assert paid.paid_at is not None

    def test_installment_group(self, session):
        prof = _make_professional(session)
        repo = ExpenseRepository(session)
        records = generate_installments("Cadeira", "material", 25000, 10, "2024-01", None, 6)
        expenses = [Expense(**r, professional_id=prof.id) for r in records]
        created = repo.create_many(expenses)
        assert len(created) == 6
        group_ids = {e.installment_group_id for e in created}
        assert len(group_ids) == 1

    def test_summary(self, session):
        prof = _make_professional(session)
        repo = ExpenseRepository(session)
        repo.create(Expense(
            professional_id=prof.id, name="A", category="aluguel",
            amount_in_cents=100000, recurrence=ExpenseRecurrence.monthly,
            reference_month="2024-03", is_paid=True,
        ))
        repo.create(Expense(
            professional_id=prof.id, name="B", category="internet",
            amount_in_cents=10000, recurrence=ExpenseRecurrence.monthly,
            reference_month="2024-03", is_paid=False,
        ))
        summary = repo.get_summary(prof.id, "2024-03")
        assert summary["total_in_cents"] == 110000
        assert summary["paid_in_cents"] == 100000
        assert summary["pending_in_cents"] == 10000
