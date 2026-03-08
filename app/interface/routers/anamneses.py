import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List

from app.infrastructure.database import get_session
from app.infrastructure.repositories.anamnesis_repository import AnamnesisRepository
from app.domain.entities.anamnesis import Anamnesis
from app.interface.dependencies import get_professional_id
from app.interface.schemas.anamnesis import AnamnesisCreate, AnamnesisUpdate, AnamnesisResponse

router = APIRouter(prefix="/anamneses", tags=["anamneses"])


@router.get("/", response_model=List[AnamnesisResponse])
def list_anamneses(
    client_id: uuid.UUID = Query(...),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AnamnesisRepository(session)
    return repo.list_by_client(professional_id, client_id)


@router.get("/{anamnesis_id}", response_model=AnamnesisResponse)
def get_anamnesis(
    anamnesis_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AnamnesisRepository(session)
    result = repo.get_by_id(professional_id, anamnesis_id)
    if not result:
        raise HTTPException(404, "Anamnesis not found")
    return result


@router.post("/", response_model=AnamnesisResponse, status_code=201)
def create_anamnesis(
    body: AnamnesisCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AnamnesisRepository(session)
    data = body.model_dump(exclude={"client_id"})
    if "mapping" in data and data["mapping"] is not None:
        data["mapping"] = body.mapping.model_dump() if body.mapping else None
    anamnesis = Anamnesis(
        professional_id=professional_id,
        client_id=body.client_id,
        **data,
    )
    return repo.create(anamnesis)


@router.put("/{anamnesis_id}", response_model=AnamnesisResponse)
def update_anamnesis(
    anamnesis_id: uuid.UUID,
    body: AnamnesisUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AnamnesisRepository(session)
    anamnesis = repo.get_by_id(professional_id, anamnesis_id)
    if not anamnesis:
        raise HTTPException(404, "Anamnesis not found")

    update_data = body.model_dump(exclude_unset=True)
    if "mapping" in update_data and update_data["mapping"] is not None:
        update_data["mapping"] = body.mapping.model_dump()

    for field, value in update_data.items():
        setattr(anamnesis, field, value)

    return repo.update(anamnesis)
