"""
Rotas de integração com serviços externos.
Atualmente: Apple Calendar via CalDAV.
"""
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.appointment_repository import AppointmentRepository
from app.domain.entities.user import User
from app.domain.enums import AppointmentStatus
from app.domain.services.apple_calendar_service import AppleCalendarService, CalendarError
from app.domain.services.crypto_service import encrypt_password, decrypt_password
from app.domain.services import calendar_sync_service
from app.interface.dependencies import get_current_user, get_professional_id

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = logging.getLogger(__name__)


# ── Schemas ────────────────────────────────────────────────────────────────────

class AppleConnectRequest(BaseModel):
    appleId: str
    appPassword: str


class AppleCalendarSelect(BaseModel):
    calendarName: str


class AppleCalendarCreate(BaseModel):
    name: str


class AppleCalendarItem(BaseModel):
    name: str
    writable: bool


class AppleStatusResponse(BaseModel):
    connected: bool
    appleId: Optional[str] = None
    calendarName: Optional[str] = None


class SyncAllResponse(BaseModel):
    synced: int
    failed: int


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_service(user: User) -> AppleCalendarService:
    if not user.apple_id or not user.apple_password_encrypted:
        raise HTTPException(400, "Apple Calendar não configurado. Conecte primeiro.")
    try:
        password = decrypt_password(user.apple_password_encrypted)
    except Exception:
        raise HTTPException(500, "Erro ao ler credenciais. Reconecte sua conta Apple.")
    return AppleCalendarService(apple_id=user.apple_id, app_password=password)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/apple-calendar/status", response_model=AppleStatusResponse)
def apple_calendar_status(current_user: User = Depends(get_current_user)):
    return AppleStatusResponse(
        connected=bool(current_user.apple_id and current_user.apple_password_encrypted),
        appleId=current_user.apple_id,
        calendarName=current_user.apple_calendar_name,
    )


@router.post("/apple-calendar/connect", response_model=AppleStatusResponse)
def apple_calendar_connect(
    body: AppleConnectRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Validates credentials against Apple iCloud and saves them encrypted."""
    try:
        svc = AppleCalendarService(apple_id=body.appleId, app_password=body.appPassword)
        svc.validate_credentials()
    except CalendarError as e:
        raise HTTPException(400, str(e))

    current_user.apple_id = body.appleId
    current_user.apple_password_encrypted = encrypt_password(body.appPassword)
    # Clear previously selected calendar when reconnecting
    current_user.apple_calendar_name = None

    repo = UserRepository(session)
    updated = repo.update(current_user)

    return AppleStatusResponse(
        connected=True,
        appleId=updated.apple_id,
        calendarName=updated.apple_calendar_name,
    )


@router.delete("/apple-calendar/disconnect", status_code=204)
def apple_calendar_disconnect(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user.apple_id = None
    current_user.apple_password_encrypted = None
    current_user.apple_calendar_name = None
    UserRepository(session).update(current_user)


@router.get("/apple-calendar/calendars", response_model=List[AppleCalendarItem])
def apple_calendar_list(current_user: User = Depends(get_current_user)):
    """Lists writable calendars from the user's iCloud account."""
    svc = _get_service(current_user)
    try:
        calendars = svc.list_calendars()
    except CalendarError as e:
        raise HTTPException(400, str(e))
    return [AppleCalendarItem(name=c["name"], writable=c["writable"]) for c in calendars]


@router.post("/apple-calendar/calendar", response_model=AppleStatusResponse)
def apple_calendar_select_or_create(
    body: AppleCalendarCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Creates a new calendar on iCloud with the given name and sets it as active."""
    svc = _get_service(current_user)
    try:
        svc.create_calendar(body.name)
    except CalendarError as e:
        raise HTTPException(400, str(e))

    current_user.apple_calendar_name = body.name
    repo = UserRepository(session)
    updated = repo.update(current_user)
    return AppleStatusResponse(
        connected=True,
        appleId=updated.apple_id,
        calendarName=updated.apple_calendar_name,
    )


@router.put("/apple-calendar/calendar", response_model=AppleStatusResponse)
def apple_calendar_set(
    body: AppleCalendarSelect,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Sets an existing calendar as the active sync target (no creation)."""
    current_user.apple_calendar_name = body.calendarName
    repo = UserRepository(session)
    updated = repo.update(current_user)
    return AppleStatusResponse(
        connected=True,
        appleId=updated.apple_id,
        calendarName=updated.apple_calendar_name,
    )


# ── Sync endpoints ────────────────────────────────────────────────────────────

_SYNCABLE_STATUSES = [AppointmentStatus.confirmed, AppointmentStatus.in_progress]


@router.post("/apple-calendar/sync-all", response_model=SyncAllResponse)
def apple_calendar_sync_all(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    """Bulk-sync all open appointments (confirmed/in_progress) that don't yet have an Apple event."""
    user = session.get(User, professional_id)
    if not user or not user.apple_id or not user.apple_calendar_name:
        raise HTTPException(400, "Apple Calendar não configurado.")

    repo = AppointmentRepository(session)
    appointments = repo.list(professional_id, statuses=_SYNCABLE_STATUSES)
    to_sync = [a for a in appointments if not a.apple_event_uid]

    synced = 0
    failed = 0
    for appt in to_sync:
        try:
            calendar_sync_service.sync_create(appt, session)
            synced += 1
        except Exception:
            failed += 1

    return SyncAllResponse(synced=synced, failed=failed)


@router.post("/apple-calendar/sync/{appointment_id}")
def apple_calendar_sync_appointment(
    appointment_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    """Sync a single appointment to Apple Calendar."""
    repo = AppointmentRepository(session)
    appt = repo.get_by_id(professional_id, appointment_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")

    user = session.get(User, professional_id)
    if not user or not user.apple_id or not user.apple_calendar_name:
        raise HTTPException(400, "Apple Calendar não configurado.")

    if appt.apple_event_uid:
        calendar_sync_service.sync_update(appt, session)
    else:
        calendar_sync_service.sync_create(appt, session)

    return {"synced": True, "appleEventUid": appt.apple_event_uid}


@router.delete("/apple-calendar/sync/{appointment_id}", status_code=200)
def apple_calendar_unsync_appointment(
    appointment_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    """Remove a single appointment from Apple Calendar."""
    repo = AppointmentRepository(session)
    appt = repo.get_by_id(professional_id, appointment_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")

    if appt.apple_event_uid:
        calendar_sync_service.sync_delete(appt, session)
        appt.apple_event_uid = None
        session.add(appt)
        session.commit()

    return {"removed": True}
