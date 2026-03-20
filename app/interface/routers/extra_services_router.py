import uuid
from datetime import datetime, timezone
from typing import Optional, List, Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel, Field

from app.infrastructure.database import get_session
from app.infrastructure.repositories.extra_service_repository import ExtraServiceRepository
from app.domain.entities.extra_service import ExtraService
from app.interface.dependencies import get_professional_id

router = APIRouter(prefix="/extra-services", tags=["extra-services"])

ExtraServiceType = Literal["add", "deduct"]


class ExtraServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    default_amount_in_cents: int = Field(default=0, ge=0)
    type: ExtraServiceType = "add"


class ExtraServiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    default_amount_in_cents: Optional[int] = Field(default=None, ge=0)
    type: Optional[ExtraServiceType] = None
    is_active: Optional[bool] = None


class ExtraServiceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    default_amount_in_cents: int
    type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=List[ExtraServiceResponse])
def list_extra_services(
    include_inactive: bool = False,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExtraServiceRepository(session)
    return repo.list(professional_id, include_inactive=include_inactive)


@router.post("/", response_model=ExtraServiceResponse, status_code=201)
def create_extra_service(
    body: ExtraServiceCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExtraServiceRepository(session)
    extra = ExtraService(
        professional_id=professional_id,
        name=body.name,
        description=body.description,
        default_amount_in_cents=body.default_amount_in_cents,
        type=body.type,
    )
    return repo.create(extra)


@router.put("/{extra_id}", response_model=ExtraServiceResponse)
def update_extra_service(
    extra_id: uuid.UUID,
    body: ExtraServiceUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExtraServiceRepository(session)
    extra = repo.get_by_id(professional_id, extra_id)
    if not extra:
        raise HTTPException(404, "Extra service not found")

    if body.name is not None:
        extra.name = body.name
    if body.description is not None:
        extra.description = body.description
    if body.default_amount_in_cents is not None:
        extra.default_amount_in_cents = body.default_amount_in_cents
    if body.type is not None:
        extra.type = body.type
    if body.is_active is not None:
        extra.is_active = body.is_active

    return repo.update(extra)


@router.delete("/{extra_id}", status_code=204)
def delete_extra_service(
    extra_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExtraServiceRepository(session)
    extra = repo.get_by_id(professional_id, extra_id)
    if not extra:
        raise HTTPException(404, "Extra service not found")
    repo.delete(extra)
