import uuid
import calendar
from datetime import datetime, date
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.infrastructure.database import get_session
from app.infrastructure.repositories.procedure_repository import ProcedureRepository
from app.infrastructure.repositories.appointment_repository import AppointmentRepository
from app.infrastructure.repositories.client_repository import ClientRepository
from app.infrastructure.repositories.time_slot_repository import TimeSlotRepository
from app.infrastructure.repositories.blocked_date_repository import BlockedDateRepository
from app.domain.entities.appointment import Appointment
from app.domain.entities.client import Client
from app.domain.entities.user import User
from app.domain.enums import AppointmentStatus
from app.domain.services.client_service import normalize_phone
from app.domain.services.slot_calculator import calculate_available_slots
from app.interface.schemas.procedure import ProcedureResponse
from app.interface.schemas.appointment import AppointmentResponse, AvailableSlotsResponse, AvailableDatesResponse
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/public", tags=["public"])


class PublicClientInput(BaseModel):
    name: str
    phone: str


class PublicAppointmentCreate(BaseModel):
    procedure_id: uuid.UUID
    scheduled_at: datetime
    client: PublicClientInput
    notes: Optional[str] = None


def _get_any_professional(session: Session) -> Optional[User]:
    """In single-tenant mode, return the first (and only) professional."""
    return session.exec(select(User).where(User.is_active == True).limit(1)).first()  # noqa: E712


@router.get("/procedures", response_model=List[ProcedureResponse])
def public_procedures(session: Session = Depends(get_session)):
    professional = _get_any_professional(session)
    if not professional:
        return []
    repo = ProcedureRepository(session)
    return repo.list(professional.id, active_only=True)


@router.get("/available-slots", response_model=AvailableSlotsResponse)
def public_available_slots(
    date: str = Query(..., description="YYYY-MM-DD"),
    procedure_id: uuid.UUID = Query(...),
    session: Session = Depends(get_session),
):
    professional = _get_any_professional(session)
    if not professional:
        return AvailableSlotsResponse(slots=[])

    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    proc_repo = ProcedureRepository(session)
    procedure = proc_repo.get_by_id(professional.id, procedure_id)
    if not procedure or not procedure.is_active:
        raise HTTPException(404, "Procedure not found or inactive")

    ts_repo = TimeSlotRepository(session)
    bd_repo = BlockedDateRepository(session)
    appt_repo = AppointmentRepository(session)

    day_of_week_js = (target_date.weekday() + 1) % 7
    time_slot = ts_repo.get_for_day(professional.id, day_of_week_js)
    blocked_dates = [b.date for b in bd_repo.list(professional.id)]
    active_appointments = appt_repo.get_active_on_date(professional.id, target_date)

    slots = calculate_available_slots(
        target_date=target_date,
        procedure_duration=procedure.duration_minutes,
        day_of_week=day_of_week_js,
        start_time=time_slot.start_time if time_slot else None,
        end_time=time_slot.end_time if time_slot else None,
        is_slot_available=time_slot.is_available if time_slot else False,
        blocked_date_strings=blocked_dates,
        existing_appointments=[(a.scheduled_at, a.ends_at) for a in active_appointments],
    )
    return AvailableSlotsResponse(slots=slots)


@router.post("/appointments", response_model=AppointmentResponse, status_code=201)
def public_create_appointment(
    body: PublicAppointmentCreate,
    session: Session = Depends(get_session),
):
    professional = _get_any_professional(session)
    if not professional:
        raise HTTPException(503, "Service unavailable")

    proc_repo = ProcedureRepository(session)
    procedure = proc_repo.get_by_id(professional.id, body.procedure_id)
    if not procedure or not procedure.is_active:
        raise HTTPException(404, "Procedure not found or inactive")

    # Find or create client by normalized phone
    client_repo = ClientRepository(session)
    phone = normalize_phone(body.client.phone)
    client = client_repo.get_by_phone(professional.id, phone)

    if not client:
        client = Client(
            professional_id=professional.id,
            name=body.client.name,
            phone=phone,
        )
        client = client_repo.create(client)

    appt = Appointment(
        professional_id=professional.id,
        client_id=client.id,
        procedure_id=body.procedure_id,
        status=AppointmentStatus.pending_approval,
        scheduled_at=body.scheduled_at,
        duration_minutes=procedure.duration_minutes,
        price_charged=procedure.price_in_cents,
        notes=body.notes,
    )
    appt_repo = AppointmentRepository(session)
    created = appt_repo.create(appt)

    response = AppointmentResponse.model_validate(created)
    response.ends_at = created.ends_at
    response.client_name = client.name
    response.client_phone = client.phone
    response.procedure_name = procedure.name
    return response
