import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.client_repository import ClientRepository
from app.domain.entities.client import Client
from app.domain.services.client_service import normalize_phone
from app.interface.dependencies import get_professional_id
from app.interface.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.interface.schemas.common import PaginatedResponse

router = APIRouter(prefix="/clients", tags=["clients"])


def _to_response(client: Client, repo: ClientRepository, professional_id: uuid.UUID) -> ClientResponse:
    total_spent, appointments_count, last_appt = repo.get_stats(professional_id, client.id)
    data = ClientResponse.model_validate(client)
    data.total_spent = total_spent
    data.appointments_count = appointments_count
    data.last_appointment_date = last_appt
    return data


@router.get("/search", response_model=List[ClientResponse])
def search_clients(
    q: str = Query(..., min_length=1),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    clients = repo.search(professional_id, q)
    return [_to_response(c, repo, professional_id) for c in clients]


@router.get("/", response_model=PaginatedResponse[ClientResponse])
def list_clients(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    clients, total = repo.list(professional_id, search=search, page=page, per_page=per_page)
    data = [_to_response(c, repo, professional_id) for c in clients]
    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    client = repo.get_by_id(professional_id, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    return _to_response(client, repo, professional_id)


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(
    body: ClientCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    phone = normalize_phone(body.phone)
    if repo.get_by_phone(professional_id, phone):
        raise HTTPException(409, detail="Phone already registered")

    client = Client(
        professional_id=professional_id,
        name=body.name,
        phone=phone,
        email=body.email,
        instagram=body.instagram,
        birthday=body.birthday,
        notes=body.notes,
        address=body.address.model_dump() if body.address else None,
    )
    created = repo.create(client)
    return _to_response(created, repo, professional_id)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: uuid.UUID,
    body: ClientUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    client = repo.get_by_id(professional_id, client_id)
    if not client:
        raise HTTPException(404, "Client not found")

    if body.name is not None:
        client.name = body.name
    if body.phone is not None:
        phone = normalize_phone(body.phone)
        existing = repo.get_by_phone(professional_id, phone)
        if existing and existing.id != client_id:
            raise HTTPException(409, "Phone already registered")
        client.phone = phone
    if body.email is not None:
        client.email = body.email
    if body.instagram is not None:
        client.instagram = body.instagram
    if body.birthday is not None:
        client.birthday = body.birthday
    if body.notes is not None:
        client.notes = body.notes
    if body.address is not None:
        client.address = body.address.model_dump()
    if body.segments is not None:
        client.segments = [s.value for s in body.segments]

    updated = repo.update(client)
    return _to_response(updated, repo, professional_id)


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    client = repo.get_by_id(professional_id, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    repo.soft_delete(client)
