import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.appointment_repository import AppointmentRepository
from app.infrastructure.repositories.procedure_repository import ProcedureRepository
from app.infrastructure.repositories.time_slot_repository import TimeSlotRepository
from app.infrastructure.repositories.blocked_date_repository import BlockedDateRepository
from app.domain.entities.appointment import Appointment
from app.domain.entities.client import Client
from app.domain.entities.procedure import Procedure
from app.domain.enums import AppointmentStatus, CancelledBy
from app.domain.services.appointment_service import validate_status_transition
from app.domain.services.slot_calculator import calculate_available_slots
from app.interface.dependencies import get_professional_id
from app.interface.schemas.appointment import (
    AppointmentCreate,
    AppointmentStatusUpdate,
    AppointmentCancelRequest,
    AppointmentResponse,
    AvailableSlotsResponse,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _to_response(appt: Appointment, session: Session) -> AppointmentResponse:
    data = AppointmentResponse.model_validate(appt)
    data.ends_at = appt.ends_at
    client = session.get(Client, appt.client_id)
    if client:
        data.client_name = client.name
        data.client_phone = client.phone
    procedure = session.get(Procedure, appt.procedure_id)
    if procedure:
        data.procedure_name = procedure.name
    return data


@router.get("/available-slots", response_model=AvailableSlotsResponse)
def available_slots(
    date: str = Query(..., description="YYYY-MM-DD"),
    procedure_id: uuid.UUID = Query(...),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    from datetime import date as date_type
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    proc_repo = ProcedureRepository(session)
    procedure = proc_repo.get_by_id(professional_id, procedure_id)
    if not procedure or not procedure.is_active:
        raise HTTPException(404, "Procedure not found or inactive")

    ts_repo = TimeSlotRepository(session)
    bd_repo = BlockedDateRepository(session)
    appt_repo = AppointmentRepository(session)

    # Python weekday(): 0=Monday, 6=Sunday
    # TimeSlot day_of_week: 0=Sunday (matches JS)
    # Convert: JS Sunday=0 → Python weekday Sunday=6
    day_of_week_python = target_date.weekday()  # 0=Mon
    day_of_week_js = (day_of_week_python + 1) % 7  # 0=Sun

    time_slot = ts_repo.get_for_day(professional_id, day_of_week_js)
    blocked_dates = [b.date for b in bd_repo.list(professional_id)]
    active_appointments = appt_repo.get_active_on_date(professional_id, target_date)

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


@router.get("/pending-approvals", response_model=List[AppointmentResponse])
def pending_approvals(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AppointmentRepository(session)
    return [_to_response(a, session) for a in repo.get_pending_approvals(professional_id)]


@router.get("/today", response_model=List[AppointmentResponse])
def today_appointments(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AppointmentRepository(session)
    return [_to_response(a, session) for a in repo.get_today(professional_id)]


@router.get("/", response_model=List[AppointmentResponse])
def list_appointments(
    client_id: Optional[uuid.UUID] = None,
    status: Optional[List[AppointmentStatus]] = Query(default=None),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AppointmentRepository(session)
    appointments = repo.list(
        professional_id,
        client_id=client_id,
        statuses=status,
        from_date=from_date,
        to_date=to_date,
    )
    return [_to_response(a, session) for a in appointments]


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AppointmentRepository(session)
    appt = repo.get_by_id(professional_id, appointment_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")
    return _to_response(appt, session)


@router.post("/", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    body: AppointmentCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    proc_repo = ProcedureRepository(session)
    procedure = proc_repo.get_by_id(professional_id, body.procedure_id)
    if not procedure:
        raise HTTPException(404, "Procedure not found")

    appt = Appointment(
        professional_id=professional_id,
        client_id=body.client_id,
        procedure_id=body.procedure_id,
        service_type=body.service_type,
        status=AppointmentStatus.pending_approval,
        scheduled_at=body.scheduled_at,
        duration_minutes=procedure.duration_minutes,
        price_charged=body.price_charged if body.price_charged is not None else procedure.price_in_cents,
        notes=body.notes,
    )
    repo = AppointmentRepository(session)
    created = repo.create(appt)
    return _to_response(created, session)


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_status(
    appointment_id: uuid.UUID,
    body: AppointmentStatusUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AppointmentRepository(session)
    appt = repo.get_by_id(professional_id, appointment_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")

    validate_status_transition(appt.status, body.status)

    if body.status == AppointmentStatus.confirmed:
        appt.confirmed_at = datetime.now(timezone.utc)

    appt.status = body.status
    updated = repo.update(appt)
    return _to_response(updated, session)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentCancelRequest,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AppointmentRepository(session)
    appt = repo.get_by_id(professional_id, appointment_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")

    validate_status_transition(appt.status, AppointmentStatus.cancelled)

    appt.status = AppointmentStatus.cancelled
    appt.cancelled_at = datetime.now(timezone.utc)
    appt.cancellation_reason = body.reason
    appt.cancelled_by = body.cancelled_by

    updated = repo.update(appt)
    return _to_response(updated, session)
