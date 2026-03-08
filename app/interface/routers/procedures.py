import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.infrastructure.database import get_session
from app.infrastructure.repositories.procedure_repository import ProcedureRepository
from app.domain.entities.procedure import Procedure
from app.interface.dependencies import get_professional_id
from app.interface.schemas.procedure import ProcedureCreate, ProcedureUpdate, ProcedureResponse

router = APIRouter(prefix="/procedures", tags=["procedures"])


@router.get("/", response_model=List[ProcedureResponse])
def list_procedures(
    active_only: bool = False,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ProcedureRepository(session)
    return repo.list(professional_id, active_only=active_only)


@router.get("/{procedure_id}", response_model=ProcedureResponse)
def get_procedure(
    procedure_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ProcedureRepository(session)
    procedure = repo.get_by_id(professional_id, procedure_id)
    if not procedure:
        raise HTTPException(404, "Procedure not found")
    return procedure


@router.post("/", response_model=ProcedureResponse, status_code=201)
def create_procedure(
    body: ProcedureCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ProcedureRepository(session)
    procedure = Procedure(**body.model_dump(), professional_id=professional_id)
    return repo.create(procedure)


@router.put("/{procedure_id}", response_model=ProcedureResponse)
def update_procedure(
    procedure_id: uuid.UUID,
    body: ProcedureUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ProcedureRepository(session)
    procedure = repo.get_by_id(professional_id, procedure_id)
    if not procedure:
        raise HTTPException(404, "Procedure not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(procedure, field, value)

    return repo.update(procedure)


@router.delete("/{procedure_id}", status_code=204)
def delete_procedure(
    procedure_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ProcedureRepository(session)
    procedure = repo.get_by_id(professional_id, procedure_id)
    if not procedure:
        raise HTTPException(404, "Procedure not found")
    repo.delete(procedure)


@router.patch("/{procedure_id}/toggle", response_model=ProcedureResponse)
def toggle_procedure(
    procedure_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ProcedureRepository(session)
    procedure = repo.get_by_id(professional_id, procedure_id)
    if not procedure:
        raise HTTPException(404, "Procedure not found")
    return repo.toggle_active(procedure)
