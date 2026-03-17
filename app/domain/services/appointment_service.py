from datetime import datetime, timedelta
from typing import List, Optional

from app.domain.entities.appointment import Appointment
from app.domain.enums import AppointmentStatus
from app.domain.exceptions import InvalidStatusTransition

# Valid transitions map
VALID_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.pending_approval: {
        AppointmentStatus.confirmed,
        AppointmentStatus.cancelled,
    },
    AppointmentStatus.confirmed: {
        AppointmentStatus.in_progress,
        AppointmentStatus.cancelled,
        AppointmentStatus.no_show,
    },
    AppointmentStatus.in_progress: {
        AppointmentStatus.completed,
        AppointmentStatus.cancelled,
    },
    AppointmentStatus.completed: set(),
    AppointmentStatus.cancelled: set(),
    AppointmentStatus.no_show: set(),
}


def find_conflict(
    scheduled_at: datetime,
    duration_minutes: int,
    existing: List[Appointment],
    exclude_id=None,
) -> Optional[Appointment]:
    """Returns the first appointment from `existing` that overlaps the new slot, or None."""
    new_end = scheduled_at + timedelta(minutes=duration_minutes)
    for appt in existing:
        if appt.id == exclude_id:
            continue
        if scheduled_at < appt.ends_at and new_end > appt.scheduled_at:
            return appt
    return None


def validate_status_transition(
    current: AppointmentStatus,
    next_status: AppointmentStatus,
) -> None:
    """Raises InvalidStatusTransition if the transition is not allowed."""
    allowed = VALID_TRANSITIONS.get(current, set())
    if next_status not in allowed:
        raise InvalidStatusTransition(
            f"Cannot transition from '{current}' to '{next_status}'. "
            f"Allowed: {[s.value for s in allowed] or 'none (final state)'}."
        )
