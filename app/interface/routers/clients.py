import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.client_repository import ClientRepository
from app.infrastructure.repositories.professional_settings_repository import ProfessionalSettingsRepository
from app.domain.entities.client import Client
from app.domain.services.client_service import normalize_phone, calculate_segments
from app.interface.dependencies import get_professional_id
from app.interface.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.interface.schemas.common import PaginatedResponse

router = APIRouter(prefix="/clients", tags=["clients"])

BEHAVIORAL_SEGMENT_VALUES = {"vip", "recorrente", "inativa"}


def _merge_segments(client: Client, appointments_count: int, total_spent: int, last_appt, rules: dict) -> list:
    """Behavioral segments computed from stats + stored technique segments from DB."""
    behavioral = [
        s.value for s in calculate_segments(
            appointments_count,
            total_spent,
            last_appt,
            vip_min_appointments=rules["vipMinAppointments"],
            vip_min_spent_cents=rules["vipMinSpentCents"],
            recorrente_max_days=rules["recorrenteMaxDays"],
            recorrente_min_appointments=rules["recorrenteMinAppointments"],
            inativa_min_days=rules["inativaMinDays"],
        )
        if s.value in BEHAVIORAL_SEGMENT_VALUES
    ]
    stored_technique = [s for s in (client.segments or []) if s not in BEHAVIORAL_SEGMENT_VALUES]
    return behavioral + stored_technique


def _to_response(client: Client, repo: ClientRepository, professional_id: uuid.UUID, rules: dict) -> ClientResponse:
    total_spent, appointments_count, last_appt, _ = repo.get_stats(professional_id, client.id)
    data = ClientResponse.model_validate(client)
    data.total_spent = total_spent
    data.appointments_count = appointments_count
    data.last_appointment_date = last_appt
    data.segments = _merge_segments(client, appointments_count, total_spent, last_appt, rules)
    return data


def _ts(d) -> float:
    """Datetime to sortable timestamp; None → 0."""
    if d is None:
        return 0.0
    if hasattr(d, "tzinfo") and d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.timestamp()


@router.get("/search", response_model=List[ClientResponse])
def search_clients(
    q: str = Query(..., min_length=1),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    rules = ProfessionalSettingsRepository(session).get_segment_rules(professional_id)
    clients = repo.search(professional_id, q)
    return [_to_response(c, repo, professional_id, rules) for c in clients]


@router.get("/", response_model=PaginatedResponse[ClientResponse])
def list_clients(
    search: Optional[str] = None,
    segments: Optional[str] = Query(None, description="Comma-separated segment names"),
    sort_by: Optional[str] = Query(None, description="most_visited|least_visited|highest_spent|last_seen_asc|last_seen_desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    rules = ProfessionalSettingsRepository(session).get_segment_rules(professional_id)
    segment_filter = [s.strip() for s in segments.split(",")] if segments else []

    if segment_filter or sort_by:
        # Fetch all + compute stats in batch → filter + sort + paginate in Python
        all_clients = repo.list_all(professional_id, search)
        stats = repo.get_stats_batch(professional_id, [c.id for c in all_clients])

        items: list = []
        for client in all_clients:
            spent, count, last = stats.get(str(client.id), (0, 0, None))
            segs = _merge_segments(client, count, spent, last, rules)
            if segment_filter and not any(s in segs for s in segment_filter):
                continue
            items.append((client, spent, count, last, segs))

        # Sort
        if sort_by == "most_visited":
            items.sort(key=lambda x: x[2], reverse=True)
        elif sort_by == "least_visited":
            items.sort(key=lambda x: x[2])
        elif sort_by == "highest_spent":
            items.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == "last_seen_asc":
            # Never seen → first (most inactive)
            items.sort(key=lambda x: (x[3] is not None, _ts(x[3])))
        elif sort_by == "last_seen_desc":
            items.sort(key=lambda x: _ts(x[3]), reverse=True)

        total = len(items)
        offset = (page - 1) * per_page
        page_items = items[offset:offset + per_page]

        data = []
        for client, spent, count, last, segs in page_items:
            r = ClientResponse.model_validate(client)
            r.total_spent = spent
            r.appointments_count = count
            r.last_appointment_date = last
            r.segments = segs
            data.append(r)

        return PaginatedResponse(data=data, total=total, page=page, per_page=per_page)

    # Fast path: DB-level pagination
    clients, total = repo.list(professional_id, search=search, page=page, per_page=per_page)
    data = [_to_response(c, repo, professional_id, rules) for c in clients]
    return PaginatedResponse(data=data, total=total, page=page, per_page=per_page)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    rules = ProfessionalSettingsRepository(session).get_segment_rules(professional_id)
    client = repo.get_by_id(professional_id, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    return _to_response(client, repo, professional_id, rules)


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(
    body: ClientCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    rules = ProfessionalSettingsRepository(session).get_segment_rules(professional_id)
    phone = normalize_phone(body.phone) if body.phone else None
    if phone and repo.get_by_phone(professional_id, phone):
        raise HTTPException(409, detail="Phone already registered")

    client = Client(
        professional_id=professional_id,
        name=body.name,
        phone=phone or "",
        email=body.email,
        instagram=body.instagram,
        birthday=body.birthday,
        notes=body.notes,
        address=body.address.model_dump() if body.address else None,
    )
    created = repo.create(client)
    return _to_response(created, repo, professional_id, rules)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: uuid.UUID,
    body: ClientUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ClientRepository(session)
    rules = ProfessionalSettingsRepository(session).get_segment_rules(professional_id)
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
        # Only store technique segments — behavioral ones are computed at read time
        technique_values = {"volume", "classic", "hybrid"}
        client.segments = [s.value for s in body.segments if s.value in technique_values]

    updated = repo.update(client)
    return _to_response(updated, repo, professional_id, rules)


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
