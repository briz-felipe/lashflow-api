"""
Background sync helpers for Apple Calendar.
All functions are best-effort — failures are logged but never surfaced to callers.
"""
import logging
from sqlmodel import Session

from app.domain.entities.appointment import Appointment
from app.domain.entities.user import User
from app.domain.entities.client import Client
from app.domain.entities.procedure import Procedure
from app.domain.services.apple_calendar_service import AppleCalendarService, CalendarError
from app.domain.services.crypto_service import decrypt_password

logger = logging.getLogger(__name__)


def _make_service(user: User) -> AppleCalendarService | None:
    if not user.apple_id or not user.apple_password_encrypted or not user.apple_calendar_name:
        return None
    try:
        password = decrypt_password(user.apple_password_encrypted)
        return AppleCalendarService(apple_id=user.apple_id, app_password=password)
    except Exception as e:
        logger.warning("calendar_sync: failed to build service for user %s: %s", user.id, e)
        return None


def sync_create(appt: Appointment, session: Session) -> None:
    """Creates a calendar event for a newly confirmed appointment."""
    user = session.get(User, appt.professional_id)
    if not user:
        return
    svc = _make_service(user)
    if not svc:
        return

    client = session.get(Client, appt.client_id)
    procedure = session.get(Procedure, appt.procedure_id)

    title = f"{procedure.name if procedure else 'Consulta'} — {client.name if client else ''}"
    location = user.salon_address or ""

    try:
        uid = svc.create_event(
            calendar_name=user.apple_calendar_name,
            title=title,
            start=appt.scheduled_at,
            end=appt.ends_at,
            description=appt.notes or "",
            location=location,
        )
        appt.apple_event_uid = uid
        session.add(appt)
        session.commit()
        logger.info("calendar_sync: created event %s for appt %s", uid, appt.id)
    except CalendarError as e:
        logger.warning("calendar_sync: create failed for appt %s: %s", appt.id, e)
    except Exception as e:
        logger.warning("calendar_sync: unexpected error for appt %s: %s", appt.id, e)


def sync_update(appt: Appointment, session: Session) -> None:
    """Updates an existing calendar event when an appointment changes."""
    if not appt.apple_event_uid:
        sync_create(appt, session)
        return

    user = session.get(User, appt.professional_id)
    if not user:
        return
    svc = _make_service(user)
    if not svc:
        return

    client = session.get(Client, appt.client_id)
    procedure = session.get(Procedure, appt.procedure_id)
    title = f"{procedure.name if procedure else 'Consulta'} — {client.name if client else ''}"

    try:
        svc.update_event(
            calendar_name=user.apple_calendar_name,
            uid=appt.apple_event_uid,
            title=title,
            start=appt.scheduled_at,
            end=appt.ends_at,
            description=appt.notes or "",
            location=user.salon_address or "",
        )
        logger.info("calendar_sync: updated event %s for appt %s", appt.apple_event_uid, appt.id)
    except CalendarError as e:
        logger.warning("calendar_sync: update failed for appt %s: %s", appt.id, e)
    except Exception as e:
        logger.warning("calendar_sync: unexpected error for appt %s: %s", appt.id, e)


def sync_delete(appt: Appointment, session: Session) -> None:
    """Removes the calendar event when an appointment is cancelled."""
    if not appt.apple_event_uid:
        return

    user = session.get(User, appt.professional_id)
    if not user:
        return
    svc = _make_service(user)
    if not svc:
        return

    try:
        svc.delete_event(calendar_name=user.apple_calendar_name, uid=appt.apple_event_uid)
        logger.info("calendar_sync: deleted event %s for appt %s", appt.apple_event_uid, appt.id)
    except CalendarError as e:
        logger.warning("calendar_sync: delete failed for appt %s: %s", appt.id, e)
    except Exception as e:
        logger.warning("calendar_sync: unexpected error for appt %s: %s", appt.id, e)
