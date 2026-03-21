import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.appointment_repository import AppointmentRepository
from app.infrastructure.repositories.procedure_repository import ProcedureRepository
from app.infrastructure.repositories.appointment_procedure_repository import AppointmentProcedureRepository
from app.infrastructure.repositories.time_slot_repository import TimeSlotRepository
from app.infrastructure.repositories.blocked_date_repository import BlockedDateRepository
from app.domain.entities.appointment import Appointment
from app.domain.entities.appointment_procedure import AppointmentProcedure
from app.domain.entities.client import Client
from app.domain.entities.procedure import Procedure
from app.domain.enums import AppointmentStatus, CancelledBy
from app.domain.services.appointment_service import validate_status_transition, find_conflict
from app.domain.exceptions import SlotUnavailable
from app.domain.services.slot_calculator import calculate_available_slots
from app.domain.services import calendar_sync_service
from app.interface.dependencies import get_professional_id
from app.interface.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatusUpdate,
    AppointmentCancelRequest,
    AppointmentResponse,
    AppointmentProcedureInput,
    AppointmentProcedureResponse,
    AvailableSlotsResponse,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _build_procedure_responses(
    appointment_id: uuid.UUID, session: Session
) -> List[AppointmentProcedureResponse]:
    ap_repo = AppointmentProcedureRepository(session)
    rows = ap_repo.get_by_appointment(appointment_id)
    result = []
    for row in rows:
        proc = session.get(Procedure, row.procedure_id)
        result.append(AppointmentProcedureResponse(
            id=row.id,
            procedure_id=row.procedure_id,
            procedure_name=proc.name if proc else "Procedimento removido",
            custom_price_in_cents=row.custom_price_in_cents,
            original_price_in_cents=row.original_price_in_cents,
            effective_price_in_cents=row.effective_price,
            duration_minutes=row.duration_minutes,
        ))
    return result


def _to_response(appt: Appointment, session: Session) -> AppointmentResponse:
    data = AppointmentResponse.model_validate(appt)
    data.ends_at = appt.ends_at
    client = session.get(Client, appt.client_id)
    if client:
        data.client_name = client.name
        data.client_phone = client.phone

    # Populate procedures array from junction table
    data.procedures = _build_procedure_responses(appt.id, session)

    # Derive procedure_name from junction table if available
    if data.procedures:
        data.procedure_name = " + ".join(p.procedure_name for p in data.procedures)
    elif appt.procedure_name_override:
        data.procedure_name = appt.procedure_name_override
    else:
        procedure = session.get(Procedure, appt.procedure_id)
        if procedure:
            data.procedure_name = procedure.name
    return data


def _create_junction_rows(
    appointment_id: uuid.UUID,
    procedures_input: List[AppointmentProcedureInput],
    professional_id: uuid.UUID,
    session: Session,
) -> tuple[int, int, List[str]]:
    """Validate and create junction rows. Returns (total_price, total_duration, names)."""
    proc_repo = ProcedureRepository(session)
    ap_repo = AppointmentProcedureRepository(session)

    rows = []
    total_price = 0
    total_duration = 0
    names = []

    for p_input in procedures_input:
        proc = proc_repo.get_by_id(professional_id, p_input.procedure_id)
        if not proc:
            raise HTTPException(404, f"Procedure {p_input.procedure_id} not found")
        if not proc.is_active:
            raise HTTPException(422, f"Procedure '{proc.name}' is inactive")

        effective_price = p_input.custom_price_in_cents if p_input.custom_price_in_cents is not None else proc.price_in_cents
        total_price += effective_price
        total_duration += proc.duration_minutes
        names.append(proc.name)

        rows.append(AppointmentProcedure(
            appointment_id=appointment_id,
            procedure_id=p_input.procedure_id,
            custom_price_in_cents=p_input.custom_price_in_cents,
            original_price_in_cents=proc.price_in_cents,
            duration_minutes=proc.duration_minutes,
        ))

    ap_repo.bulk_create(rows)
    return total_price, total_duration, names


@router.get("/available-slots", response_model=AvailableSlotsResponse)
def available_slots(
    date: str = Query(..., description="YYYY-MM-DD"),
    procedure_id: uuid.UUID = Query(...),
    duration_minutes: Optional[int] = Query(default=None, description="Override duration for multi-procedure"),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    proc_repo = ProcedureRepository(session)
    procedure = proc_repo.get_by_id(professional_id, procedure_id)
    if not procedure or not procedure.is_active:
        raise HTTPException(404, "Procedure not found or inactive")

    effective_duration = duration_minutes or procedure.duration_minutes

    ts_repo = TimeSlotRepository(session)
    bd_repo = BlockedDateRepository(session)
    appt_repo = AppointmentRepository(session)

    day_of_week_python = target_date.weekday()
    day_of_week_js = (day_of_week_python + 1) % 7

    time_slot = ts_repo.get_for_day(professional_id, day_of_week_js)
    blocked_dates = [b.date for b in bd_repo.list(professional_id)]
    active_appointments = appt_repo.get_active_on_date(professional_id, target_date)

    slots = calculate_available_slots(
        target_date=target_date,
        procedure_duration=effective_duration,
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
    background_tasks: BackgroundTasks,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    use_multi = body.procedures and len(body.procedures) > 0

    if use_multi:
        # Multi-procedure path: validate all procedures and compute totals
        proc_repo = ProcedureRepository(session)
        total_price = 0
        total_duration = 0
        names = []
        for p_input in body.procedures:
            proc = proc_repo.get_by_id(professional_id, p_input.procedure_id)
            if not proc:
                raise HTTPException(404, f"Procedure {p_input.procedure_id} not found")
            if not proc.is_active:
                raise HTTPException(422, f"Procedure '{proc.name}' is inactive")
            ep = p_input.custom_price_in_cents if p_input.custom_price_in_cents is not None else proc.price_in_cents
            total_price += ep
            total_duration += proc.duration_minutes
            names.append(proc.name)

        primary_procedure_id = body.procedures[0].procedure_id
        effective_duration = body.duration_minutes or total_duration
        effective_price = body.price_charged if body.price_charged is not None else total_price
        combined_name = " + ".join(names) if len(names) > 1 else None
    else:
        # Legacy single-procedure path
        if not body.procedure_id:
            raise HTTPException(422, "Either procedure_id or procedures must be provided")
        proc_repo = ProcedureRepository(session)
        procedure = proc_repo.get_by_id(professional_id, body.procedure_id)
        if not procedure:
            raise HTTPException(404, "Procedure not found")

        primary_procedure_id = body.procedure_id
        effective_duration = body.duration_minutes or procedure.duration_minutes
        effective_price = body.price_charged if body.price_charged is not None else procedure.price_in_cents
        combined_name = body.procedure_name if body.procedure_name else None

    repo = AppointmentRepository(session)
    existing = repo.get_active_on_date(professional_id, body.scheduled_at.date())
    conflict = find_conflict(body.scheduled_at, effective_duration, existing)
    if conflict:
        conflict_client = session.get(Client, conflict.client_id)
        client_name = conflict_client.name if conflict_client else "outro cliente"
        raise SlotUnavailable(
            f"Horário indisponível: {client_name} já tem agendamento nesse horário."
        )

    initial_status = body.status or AppointmentStatus.pending_approval
    appt = Appointment(
        professional_id=professional_id,
        client_id=body.client_id,
        procedure_id=primary_procedure_id,
        service_type=body.service_type,
        status=initial_status,
        scheduled_at=body.scheduled_at,
        duration_minutes=effective_duration,
        price_charged=effective_price,
        notes=body.notes,
        procedure_name_override=combined_name,
    )
    created = repo.create(appt)

    # Create junction rows
    if use_multi:
        _create_junction_rows(created.id, body.procedures, professional_id, session)
    else:
        # Legacy path: still create a single junction row for consistency
        proc = proc_repo.get_by_id(professional_id, primary_procedure_id)
        ap_repo = AppointmentProcedureRepository(session)
        ap_repo.bulk_create([AppointmentProcedure(
            appointment_id=created.id,
            procedure_id=primary_procedure_id,
            custom_price_in_cents=body.price_charged if body.price_charged is not None and proc and body.price_charged != proc.price_in_cents else None,
            original_price_in_cents=proc.price_in_cents if proc else effective_price,
            duration_minutes=proc.duration_minutes if proc else effective_duration,
        )])

    # Sync confirmed appointments to Apple Calendar
    if initial_status == AppointmentStatus.confirmed:
        background_tasks.add_task(calendar_sync_service.sync_create, created, session)

    return _to_response(created, session)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentUpdate,
    background_tasks: BackgroundTasks,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = AppointmentRepository(session)
    appt = repo.get_by_id(professional_id, appointment_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")

    # Handle multi-procedure update
    if body.procedures is not None:
        ap_repo = AppointmentProcedureRepository(session)
        proc_repo = ProcedureRepository(session)

        # Validate and build new junction rows
        rows = []
        total_price = 0
        total_duration = 0
        names = []
        for p_input in body.procedures:
            proc = proc_repo.get_by_id(professional_id, p_input.procedure_id)
            if not proc:
                raise HTTPException(404, f"Procedure {p_input.procedure_id} not found")
            if not proc.is_active:
                raise HTTPException(422, f"Procedure '{proc.name}' is inactive")
            ep = p_input.custom_price_in_cents if p_input.custom_price_in_cents is not None else proc.price_in_cents
            total_price += ep
            total_duration += proc.duration_minutes
            names.append(proc.name)
            rows.append(AppointmentProcedure(
                appointment_id=appointment_id,
                procedure_id=p_input.procedure_id,
                custom_price_in_cents=p_input.custom_price_in_cents,
                original_price_in_cents=proc.price_in_cents,
                duration_minutes=proc.duration_minutes,
            ))

        ap_repo.replace_for_appointment(appointment_id, rows)

        # Update legacy fields from junction data
        appt.procedure_id = body.procedures[0].procedure_id
        appt.price_charged = body.price_charged if body.price_charged is not None else total_price
        appt.duration_minutes = body.duration_minutes if body.duration_minutes is not None else total_duration
        appt.procedure_name_override = " + ".join(names) if len(names) > 1 else None
    else:
        # Legacy single-procedure update
        if body.procedure_id is not None:
            proc_repo = ProcedureRepository(session)
            procedure = proc_repo.get_by_id(professional_id, body.procedure_id)
            if not procedure:
                raise HTTPException(404, "Procedure not found")
            appt.procedure_id = body.procedure_id

        if body.price_charged is not None:
            appt.price_charged = body.price_charged
        if body.duration_minutes is not None:
            appt.duration_minutes = body.duration_minutes
        if body.procedure_name is not None:
            appt.procedure_name_override = body.procedure_name if body.procedure_name else None

    if body.scheduled_at is not None:
        effective_duration = appt.duration_minutes
        existing = repo.get_active_on_date(professional_id, body.scheduled_at.date())
        conflict = find_conflict(body.scheduled_at, effective_duration, existing, exclude_id=appt.id)
        if conflict:
            conflict_client = session.get(Client, conflict.client_id)
            client_name = conflict_client.name if conflict_client else "outro cliente"
            raise SlotUnavailable(
                f"Horário indisponível: {client_name} já tem agendamento nesse horário."
            )
        appt.scheduled_at = body.scheduled_at

    if body.service_type is not None:
        appt.service_type = body.service_type
    if body.notes is not None:
        appt.notes = body.notes if body.notes else None

    appt.updated_at = datetime.now(timezone.utc)
    updated = repo.update(appt)
    return _to_response(updated, session)


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_status(
    appointment_id: uuid.UUID,
    body: AppointmentStatusUpdate,
    background_tasks: BackgroundTasks,
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

    # Sync to Apple Calendar
    if body.status == AppointmentStatus.confirmed:
        background_tasks.add_task(calendar_sync_service.sync_create, updated, session)
    elif body.status == AppointmentStatus.cancelled:
        background_tasks.add_task(calendar_sync_service.sync_delete, updated, session)

    return _to_response(updated, session)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentCancelRequest,
    background_tasks: BackgroundTasks,
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
    background_tasks.add_task(calendar_sync_service.sync_delete, updated, session)
    return _to_response(updated, session)
