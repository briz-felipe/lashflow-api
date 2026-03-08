from app.domain.enums import ExpenseRecurrence
from app.domain.services.expense_service import generate_installments


class TestGenerateInstallments:
    def test_generates_correct_count(self):
        records = generate_installments("Test", "aluguel", 10000, 5, "2024-01", None, 3)
        assert len(records) == 3

    def test_installment_current_is_sequential(self):
        records = generate_installments("Test", "aluguel", 10000, 5, "2024-01", None, 3)
        assert [r["installment_current"] for r in records] == [1, 2, 3]

    def test_installment_total_same_on_all(self):
        records = generate_installments("Test", "aluguel", 10000, 5, "2024-01", None, 6)
        assert all(r["installment_total"] == 6 for r in records)

    def test_months_increment_correctly(self):
        records = generate_installments("Test", "aluguel", 10000, 5, "2024-01", None, 3)
        assert records[0]["reference_month"] == "2024-01"
        assert records[1]["reference_month"] == "2024-02"
        assert records[2]["reference_month"] == "2024-03"

    def test_month_wraps_to_next_year(self):
        records = generate_installments("Test", "aluguel", 10000, 5, "2024-11", None, 3)
        assert records[0]["reference_month"] == "2024-11"
        assert records[1]["reference_month"] == "2024-12"
        assert records[2]["reference_month"] == "2025-01"

    def test_recurrence_forced_to_monthly(self):
        records = generate_installments("Test", "aluguel", 10000, 5, "2024-01", None, 2)
        assert all(r["recurrence"] == ExpenseRecurrence.monthly for r in records)

    def test_all_share_same_group_id(self):
        records = generate_installments("Test", "aluguel", 10000, 5, "2024-01", None, 4)
        group_ids = {r["installment_group_id"] for r in records}
        assert len(group_ids) == 1

    def test_amount_is_same_on_all(self):
        records = generate_installments("Test", "aluguel", 25000, 5, "2024-01", None, 6)
        assert all(r["amount_in_cents"] == 25000 for r in records)

    def test_single_installment(self):
        records = generate_installments("Test", "aluguel", 10000, 5, "2024-01", None, 1)
        assert len(records) == 1
        assert records[0]["installment_current"] == 1
