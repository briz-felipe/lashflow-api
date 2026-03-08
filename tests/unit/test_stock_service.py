import pytest
from app.domain.enums import StockMovementType
from app.domain.exceptions import InsufficientStock
from app.domain.services.stock_service import apply_movement, is_low_stock


class TestApplyMovement:
    def test_purchase_increases_stock(self):
        assert apply_movement(10, StockMovementType.purchase, 5) == 15

    def test_usage_decreases_stock(self):
        assert apply_movement(10, StockMovementType.usage, 5) == 5

    def test_usage_exact_zero(self):
        assert apply_movement(5, StockMovementType.usage, 5) == 0

    def test_usage_insufficient_raises(self):
        with pytest.raises(InsufficientStock):
            apply_movement(3, StockMovementType.usage, 5)

    def test_adjustment_sets_absolute(self):
        assert apply_movement(100, StockMovementType.adjustment, 42) == 42

    def test_adjustment_to_zero(self):
        assert apply_movement(100, StockMovementType.adjustment, 0) == 0

    def test_purchase_from_zero(self):
        assert apply_movement(0, StockMovementType.purchase, 10) == 10


class TestIsLowStock:
    def test_below_minimum(self):
        assert is_low_stock(3, 5) is True

    def test_at_minimum(self):
        assert is_low_stock(5, 5) is True

    def test_above_minimum(self):
        assert is_low_stock(6, 5) is False
