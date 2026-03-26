import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.repositories.stock_movement_repository import StockMovementRepository
from app.domain.entities.material import Material
from app.domain.entities.stock_movement import StockMovement
from app.domain.services.stock_service import apply_movement, is_low_stock
from app.interface.dependencies import get_professional_id
from app.interface.schemas.material import (
    MaterialCreate, MaterialUpdate, MaterialResponse, StockValueResponse
)
from app.interface.schemas.stock_movement import StockMovementCreate, StockMovementUpdate, StockMovementResponse

router = APIRouter(prefix="/stock", tags=["stock"])

# --- Materials ---


@router.get("/materials/alerts", response_model=List[MaterialResponse])
def low_stock_alerts(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = MaterialRepository(session)
    return repo.list(professional_id, low_stock=True)


@router.get("/value", response_model=StockValueResponse)
def stock_value(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = MaterialRepository(session)
    total = repo.get_total_stock_value(professional_id)
    return StockValueResponse(total_value_in_cents=total)


@router.get("/monthly-costs")
def monthly_costs(
    months: int = Query(6, ge=1, le=24),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = MaterialRepository(session)
    return repo.get_monthly_costs(professional_id, months)


@router.get("/materials", response_model=List[MaterialResponse])
def list_materials(
    category: Optional[str] = None,
    search: Optional[str] = None,
    low_stock: bool = False,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = MaterialRepository(session)
    return repo.list(professional_id, category=category, search=search, low_stock=low_stock)


@router.get("/materials/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = MaterialRepository(session)
    material = repo.get_by_id(professional_id, material_id)
    if not material:
        raise HTTPException(404, "Material not found")
    return material


@router.post("/materials", response_model=MaterialResponse, status_code=201)
def create_material(
    body: MaterialCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = MaterialRepository(session)
    material = Material(**body.model_dump(), professional_id=professional_id)
    return repo.create(material)


@router.put("/materials/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: uuid.UUID,
    body: MaterialUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = MaterialRepository(session)
    material = repo.get_by_id(professional_id, material_id)
    if not material:
        raise HTTPException(404, "Material not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(material, field, value)
    return repo.update(material)


@router.delete("/materials/{material_id}", status_code=204)
def delete_material(
    material_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = MaterialRepository(session)
    material = repo.get_by_id(professional_id, material_id)
    if not material:
        raise HTTPException(404, "Material not found")
    repo.deactivate(material)


# --- Movements ---


@router.get("/movements", response_model=List[StockMovementResponse])
def list_movements(
    material_id: Optional[uuid.UUID] = None,
    expense_id: Optional[uuid.UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = StockMovementRepository(session)
    rows = repo.list_with_material_name(
        professional_id, material_id=material_id, expense_id=expense_id,
        from_date=from_date, to_date=to_date,
    )
    result = []
    for movement, material_name in rows:
        item = StockMovementResponse.model_validate(movement)
        item.material_name = material_name
        result.append(item)
    return result


@router.post("/movements", response_model=StockMovementResponse, status_code=201)
def create_movement(
    body: StockMovementCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    material_repo = MaterialRepository(session)
    material = material_repo.get_by_id(professional_id, body.material_id)
    if not material:
        raise HTTPException(404, "Material not found")

    # Domain service validates and computes new stock (raises InsufficientStock if needed)
    new_stock = apply_movement(material.current_stock, body.type, body.quantity)

    # Validate expense link if provided
    if body.expense_id:
        from app.infrastructure.repositories.expense_repository import ExpenseRepository
        expense_repo = ExpenseRepository(session)
        expense = expense_repo.get_by_id(professional_id, body.expense_id)
        if not expense:
            raise HTTPException(404, "Expense not found")
        if expense.category != "material":
            raise HTTPException(422, "Expense must have category 'material'")

    movement = StockMovement(
        professional_id=professional_id,
        material_id=body.material_id,
        type=body.type,
        quantity=body.quantity,
        unit_cost_in_cents=body.unit_cost_in_cents,
        total_cost_in_cents=body.quantity * body.unit_cost_in_cents,
        expense_id=body.expense_id,
        notes=body.notes,
    )
    movement_repo = StockMovementRepository(session)
    created = movement_repo.create_with_stock_update(movement, material, new_stock)
    item = StockMovementResponse.model_validate(created)
    item.material_name = material.name
    return item


def _stock_delta(movement: StockMovement) -> int:
    """Returns the stock change caused by a movement (positive = added stock)."""
    from app.domain.enums import StockMovementType as SMT
    if movement.type == SMT.purchase:
        return movement.quantity
    elif movement.type == SMT.usage:
        return -movement.quantity
    return 0  # adjustment doesn't have a simple delta


@router.put("/movements/{movement_id}", response_model=StockMovementResponse)
def update_movement(
    movement_id: uuid.UUID,
    body: StockMovementUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    movement_repo = StockMovementRepository(session)
    movement = movement_repo.get_by_id(professional_id, movement_id)
    if not movement:
        raise HTTPException(404, "Movement not found")

    material_repo = MaterialRepository(session)
    material = material_repo.get_by_id(professional_id, movement.material_id)
    if not material:
        raise HTTPException(404, "Material not found")

    old_delta = _stock_delta(movement)

    # Apply updates
    if body.quantity is not None:
        movement.quantity = body.quantity
        movement.total_cost_in_cents = body.quantity * (
            body.unit_cost_in_cents if body.unit_cost_in_cents is not None else movement.unit_cost_in_cents
        )
    if body.unit_cost_in_cents is not None:
        movement.unit_cost_in_cents = body.unit_cost_in_cents
        movement.total_cost_in_cents = movement.quantity * body.unit_cost_in_cents
    if body.expense_id is not None:
        movement.expense_id = body.expense_id if str(body.expense_id) != "00000000-0000-0000-0000-000000000000" else None
    if body.notes is not None:
        movement.notes = body.notes or None

    new_delta = _stock_delta(movement)

    updated = movement_repo.update_with_stock_adjustment(movement, material, old_delta, new_delta)
    item = StockMovementResponse.model_validate(updated)
    item.material_name = material.name
    return item


@router.delete("/movements/{movement_id}", status_code=204)
def delete_movement(
    movement_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    movement_repo = StockMovementRepository(session)
    movement = movement_repo.get_by_id(professional_id, movement_id)
    if not movement:
        raise HTTPException(404, "Movement not found")

    material_repo = MaterialRepository(session)
    material = material_repo.get_by_id(professional_id, movement.material_id)
    if not material:
        raise HTTPException(404, "Material not found")

    delta = _stock_delta(movement)
    movement_repo.delete_with_stock_rollback(movement, material, delta)
