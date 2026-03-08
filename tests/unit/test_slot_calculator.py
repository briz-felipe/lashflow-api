from datetime import date, datetime
from app.domain.services.slot_calculator import calculate_available_slots


def _slots(
    target_date=None,
    duration=60,
    start_time="09:00",
    end_time="18:00",
    is_available=True,
    blocked=[],
    appointments=[],
    now=None,
):
    if target_date is None:
        target_date = date(2030, 1, 6)  # Monday, far future
    if now is None:
        now = datetime(2030, 1, 6, 0, 0, 0)  # midnight same day
    return calculate_available_slots(
        target_date=target_date,
        procedure_duration=duration,
        day_of_week=1,  # Monday in JS convention
        start_time=start_time,
        end_time=end_time,
        is_slot_available=is_available,
        blocked_date_strings=blocked,
        existing_appointments=appointments,
        now=now,
    )


class TestSlotCalculator:
    def test_returns_slots_in_range(self):
        result = _slots(duration=60, start_time="09:00", end_time="11:00")
        assert "2030-01-06T09:00:00" in result
        assert "2030-01-06T09:30:00" in result
        assert "2030-01-06T10:00:00" in result
        # 10:30 + 60 min = 11:30 > 11:00 → excluded
        assert "2030-01-06T10:30:00" not in result

    def test_blocked_date_returns_empty(self):
        result = _slots(blocked=["2030-01-06"])
        assert result == []

    def test_unavailable_day_returns_empty(self):
        result = _slots(is_available=False)
        assert result == []

    def test_no_time_slot_returns_empty(self):
        result = _slots(start_time=None, end_time=None, is_available=False)
        assert result == []

    def test_excludes_past_slots(self):
        # now is at 10:00 — slots at 09:00 and 09:30 should be excluded
        now = datetime(2030, 1, 6, 10, 0, 0)
        result = _slots(start_time="09:00", end_time="12:00", duration=30, now=now)
        assert "2030-01-06T09:00:00" not in result
        assert "2030-01-06T09:30:00" not in result
        assert "2030-01-06T10:30:00" in result

    def test_excludes_conflicting_appointments(self):
        # Existing appointment: 09:00–10:00
        appt_start = datetime(2030, 1, 6, 9, 0)
        appt_end = datetime(2030, 1, 6, 10, 0)
        result = _slots(duration=60, start_time="09:00", end_time="12:00", appointments=[(appt_start, appt_end)])
        assert "2030-01-06T09:00:00" not in result
        # 09:30 + 60 min = 10:30, overlaps with 09:00–10:00
        assert "2030-01-06T09:30:00" not in result
        # 10:00 + 60 min = 11:00, no overlap
        assert "2030-01-06T10:00:00" in result

    def test_procedure_must_fit_before_end(self):
        # 120-min procedure, 1-hour window → no slots
        result = _slots(duration=120, start_time="09:00", end_time="10:00")
        assert result == []

    def test_30_min_slots_generated(self):
        result = _slots(duration=30, start_time="09:00", end_time="10:00")
        assert "2030-01-06T09:00:00" in result
        assert "2030-01-06T09:30:00" in result
        assert len(result) == 2
