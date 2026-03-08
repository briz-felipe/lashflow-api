from app.domain.enums import PaymentStatus
from app.domain.services.payment_service import calculate_payment_status, sum_partial_payments


class TestCalculatePaymentStatus:
    def test_zero_paid_is_pending(self):
        assert calculate_payment_status(0, 10000) == PaymentStatus.pending

    def test_negative_paid_is_pending(self):
        assert calculate_payment_status(-1, 10000) == PaymentStatus.pending

    def test_partial_payment(self):
        assert calculate_payment_status(5000, 10000) == PaymentStatus.partial

    def test_exact_full_payment(self):
        assert calculate_payment_status(10000, 10000) == PaymentStatus.paid

    def test_overpayment_is_paid(self):
        assert calculate_payment_status(12000, 10000) == PaymentStatus.paid

    def test_one_cent_is_partial(self):
        assert calculate_payment_status(1, 10000) == PaymentStatus.partial


class TestSumPartialPayments:
    def test_empty_list(self):
        assert sum_partial_payments([]) == 0

    def test_single(self):
        assert sum_partial_payments([5000]) == 5000

    def test_multiple(self):
        assert sum_partial_payments([3000, 2000, 5000]) == 10000
