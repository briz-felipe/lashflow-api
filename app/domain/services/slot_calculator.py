from datetime import date, datetime, timedelta
from typing import Optional, List


def _parse_time(time_str: str, ref_date: date) -> datetime:
    """Convert 'HH:MM' string to a datetime on the given date (UTC naive)."""
    h, m = map(int, time_str.split(":"))
    return datetime(ref_date.year, ref_date.month, ref_date.day, h, m)


def calculate_available_slots(
    target_date: date,
    procedure_duration: int,
    day_of_week: int,  # 0=Monday (Python weekday()) — NOT Sunday
    start_time: Optional[str],  # "HH:MM" or None if no slot configured
    end_time: Optional[str],
    is_slot_available: bool,
    blocked_date_strings: List[str],  # "YYYY-MM-DD"
    existing_appointments: List[tuple[datetime, datetime]],  # (starts_at, ends_at)
    now: Optional[datetime] = None,
) -> List[str]:
    """
    Pure function — no DB access.

    Returns a list of ISO 8601 datetime strings representing available slots.

    Implements the 7-step algorithm from the readme (section 4.1):
    1. Check blocked dates
    2. Check day of week has a time slot and is_available
    3. Generate slots every 30 minutes
    4. Filter by procedure fits within end_time
    5. Exclude slots conflicting with existing appointments
    6. Exclude past slots
    7. Return remaining

    Note: existing_appointments should only include non-cancelled/no_show appointments.
    """
    now = now or datetime.utcnow()
    target_str = target_date.strftime("%Y-%m-%d")

    # Step 1: blocked date
    if target_str in blocked_date_strings:
        return []

    # Step 2: slot must exist and be available
    if not is_slot_available or start_time is None or end_time is None:
        return []

    slot_start = _parse_time(start_time, target_date)
    slot_end = _parse_time(end_time, target_date)

    # Step 3 & 4: generate 30-min slots where procedure fits
    available: List[str] = []
    current = slot_start
    slot_delta = timedelta(minutes=30)
    proc_delta = timedelta(minutes=procedure_duration)

    while current + proc_delta <= slot_end:
        candidate_end = current + proc_delta

        # Step 6: skip past slots
        if current <= now:
            current += slot_delta
            continue

        # Step 5: check conflicts with existing appointments
        conflict = any(
            current < appt_end and candidate_end > appt_start
            for appt_start, appt_end in existing_appointments
        )

        if not conflict:
            available.append(current.strftime("%Y-%m-%dT%H:%M:%S"))

        current += slot_delta

    return available
