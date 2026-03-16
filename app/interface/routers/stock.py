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
from app.interface.schemas.stock_movement import StockMovementCreate, StockMovementResponse

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
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = StockMovementRepository(session)
    rows = repo.list_with_material_name(
        professional_id, material_id=material_id, from_date=from_date, to_date=to_date
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

    movement = StockMovement(
        professional_id=professional_id,
        material_id=body.material_id,
        type=body.type,
        quantity=body.quantity,
        unit_cost_in_cents=body.unit_cost_in_cents,
        total_cost_in_cents=body.quantity * body.unit_cost_in_cents,
        notes=body.notes,
    )
    movement_repo = StockMovementRepository(session)
    created = movement_repo.create_with_stock_update(movement, material, new_stock)
    item = StockMovementResponse.model_validate(created)
    item.material_name = material.name
    return item
