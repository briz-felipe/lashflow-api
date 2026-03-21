import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.infrastructure.database import get_session
from app.infrastructure.repositories.procedure_repository import ProcedureRepository
from app.infrastructure.repositories.appointment_repository import AppointmentRepository
from app.infrastructure.repositories.appointment_procedure_repository import AppointmentProcedureRepository
from app.infrastructure.repositories.client_repository import ClientRepository
from app.infrastructure.repositories.time_slot_repository import TimeSlotRepository
from app.infrastructure.repositories.blocked_date_repository import BlockedDateRepository
from app.domain.entities.appointment import Appointment
from app.domain.entities.appointment_procedure import AppointmentProcedure
from app.domain.entities.client import Client
from app.domain.entities.user import User
from app.domain.enums import AppointmentStatus
from app.domain.services.client_service import normalize_phone
from app.domain.services.slot_calculator import calculate_available_slots
from app.interface.schemas.procedure import ProcedureResponse
from app.interface.schemas.appointment import AppointmentResponse, AppointmentProcedureResponse, AvailableSlotsResponse
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/public", tags=["public"])


class PublicClientInput(BaseModel):
    name: str
    phone: str


class PublicProcedureInput(BaseModel):
    procedure_id: uuid.UUID


class PublicAppointmentCreate(BaseModel):
    procedure_id: Optional[uuid.UUID] = None  # legacy single
    procedures: Optional[List[PublicProcedureInput]] = None  # new multi
    scheduled_at: datetime
    client: PublicClientInput
    notes: Optional[str] = None
    slug: str


class PublicSalonResponse(BaseModel):
    slug: str
    salon_name: Optional[str] = None
    salon_address: Optional[str] = None


def _get_professional_by_slug(slug: str, session: Session) -> Optional[User]:
    """Look up professional by salon_slug; fallback to username for users without a slug."""
    user = session.exec(
        select(User).where(User.salon_slug == slug, User.is_active == True)  # noqa: E712
    ).first()
    if user:
        return user
    # Fallback: allow login username as slug (users who haven't configured salon_slug yet)
    return session.exec(
        select(User).where(User.username == slug, User.is_active == True)  # noqa: E712
    ).first()


@router.get("/salon/{slug}", response_model=PublicSalonResponse)
def public_salon_info(slug: str, session: Session = Depends(get_session)):
    professional = _get_professional_by_slug(slug, session)
    if not professional:
        raise HTTPException(404, "Salon not found")
    return PublicSalonResponse(
        slug=slug,
        salon_name=professional.salon_name,
        salon_address=professional.salon_address,
    )


@router.get("/procedures", response_model=List[ProcedureResponse])
def public_procedures(
    slug: str = Query(..., description="Salon slug"),
    session: Session = Depends(get_session),
):
    professional = _get_professional_by_slug(slug, session)
    if not professional:
        raise HTTPException(404, "Salon not found")
    repo = ProcedureRepository(session)
    return repo.list(professional.id, active_only=True)


@router.get("/available-slots", response_model=AvailableSlotsResponse)
def public_available_slots(
    slug: str = Query(..., description="Salon slug"),
    date: str = Query(..., description="YYYY-MM-DD"),
    procedure_id: uuid.UUID = Query(...),
    session: Session = Depends(get_session),
):
    professional = _get_professional_by_slug(slug, session)
    if not professional:
        raise HTTPException(404, "Salon not found")

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


def _build_public_procedure_responses(
    appointment_id: uuid.UUID, session: Session
) -> List[AppointmentProcedureResponse]:
    from app.domain.entities.procedure import Procedure as ProcEntity
    ap_repo = AppointmentProcedureRepository(session)
    rows = ap_repo.get_by_appointment(appointment_id)
    result = []
    for row in rows:
        proc = session.get(ProcEntity, row.procedure_id)
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


@router.post("/appointments", response_model=AppointmentResponse, status_code=201)
def public_create_appointment(
    body: PublicAppointmentCreate,
    session: Session = Depends(get_session),
):
    professional = _get_professional_by_slug(body.slug, session)
    if not professional:
        raise HTTPException(404, "Salon not found")

    proc_repo = ProcedureRepository(session)
    use_multi = body.procedures and len(body.procedures) > 0

    if use_multi:
        # Multi-procedure public booking
        procedures = []
        total_price = 0
        total_duration = 0
        names = []
        for p_input in body.procedures:
            proc = proc_repo.get_by_id(professional.id, p_input.procedure_id)
            if not proc or not proc.is_active:
                raise HTTPException(404, f"Procedure {p_input.procedure_id} not found or inactive")
            procedures.append(proc)
            total_price += proc.price_in_cents
            total_duration += proc.duration_minutes
            names.append(proc.name)

        primary_procedure_id = body.procedures[0].procedure_id
        combined_name = " + ".join(names) if len(names) > 1 else None
    else:
        # Legacy single-procedure path
        if not body.procedure_id:
            raise HTTPException(422, "Either procedure_id or procedures must be provided")
        procedure = proc_repo.get_by_id(professional.id, body.procedure_id)
        if not procedure or not procedure.is_active:
            raise HTTPException(404, "Procedure not found or inactive")
        primary_procedure_id = body.procedure_id
        total_price = procedure.price_in_cents
        total_duration = procedure.duration_minutes
        procedures = [procedure]
        combined_name = None

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
        procedure_id=primary_procedure_id,
        status=AppointmentStatus.pending_approval,
        scheduled_at=body.scheduled_at,
        duration_minutes=total_duration,
        price_charged=total_price,
        notes=body.notes,
        procedure_name_override=combined_name,
    )
    appt_repo = AppointmentRepository(session)
    created = appt_repo.create(appt)

    # Create junction rows
    ap_repo = AppointmentProcedureRepository(session)
    junction_rows = [
        AppointmentProcedure(
            appointment_id=created.id,
            procedure_id=proc.id,
            custom_price_in_cents=None,  # public bookings always use table price
            original_price_in_cents=proc.price_in_cents,
            duration_minutes=proc.duration_minutes,
        )
        for proc in procedures
    ]
    ap_repo.bulk_create(junction_rows)

    response = AppointmentResponse.model_validate(created)
    response.ends_at = created.ends_at
    response.client_name = client.name
    response.client_phone = client.phone
    response.procedures = _build_public_procedure_responses(created.id, session)
    response.procedure_name = " + ".join(p.procedure_name for p in response.procedures) if response.procedures else procedures[0].name
    return response
