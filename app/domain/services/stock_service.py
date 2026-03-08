from app.domain.enums import StockMovementType
from app.domain.exceptions import InsufficientStock


def apply_movement(
    current_stock: int,
    movement_type: StockMovementType,
    quantity: int,
) -> int:
    """
    Computes the new stock value after a movement.

    - purchase:   current_stock + quantity
    - usage:      current_stock - quantity (raises InsufficientStock if result < 0)
    - adjustment: quantity (absolute value — new stock level)
    """
    if movement_type == StockMovementType.purchase:
        return current_stock + quantity

    if movement_type == StockMovementType.usage:
        new_stock = current_stock - quantity
        if new_stock < 0:
            raise InsufficientStock(
                f"Insufficient stock: current={current_stock}, requested={quantity}."
            )
        return new_stock

    if movement_type == StockMovementType.adjustment:
        return quantity

    raise ValueError(f"Unknown movement type: {movement_type}")


def is_low_stock(current_stock: int, minimum_stock: int) -> bool:
    return current_stock <= minimum_stock
