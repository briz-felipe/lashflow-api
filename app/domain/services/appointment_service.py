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
