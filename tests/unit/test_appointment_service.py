import pytest
from app.domain.enums import AppointmentStatus
from app.domain.exceptions import InvalidStatusTransition
from app.domain.services.appointment_service import validate_status_transition


class TestValidStatusTransitions:
    def test_pending_to_confirmed(self):
        validate_status_transition(AppointmentStatus.pending_approval, AppointmentStatus.confirmed)

    def test_pending_to_cancelled(self):
        validate_status_transition(AppointmentStatus.pending_approval, AppointmentStatus.cancelled)

    def test_confirmed_to_in_progress(self):
        validate_status_transition(AppointmentStatus.confirmed, AppointmentStatus.in_progress)

    def test_confirmed_to_cancelled(self):
        validate_status_transition(AppointmentStatus.confirmed, AppointmentStatus.cancelled)

    def test_confirmed_to_no_show(self):
        validate_status_transition(AppointmentStatus.confirmed, AppointmentStatus.no_show)

    def test_in_progress_to_completed(self):
        validate_status_transition(AppointmentStatus.in_progress, AppointmentStatus.completed)

    def test_in_progress_to_cancelled(self):
        validate_status_transition(AppointmentStatus.in_progress, AppointmentStatus.cancelled)


class TestInvalidStatusTransitions:
    def test_completed_is_final(self):
        with pytest.raises(InvalidStatusTransition):
            validate_status_transition(AppointmentStatus.completed, AppointmentStatus.confirmed)

    def test_cancelled_is_final(self):
        with pytest.raises(InvalidStatusTransition):
            validate_status_transition(AppointmentStatus.cancelled, AppointmentStatus.confirmed)

    def test_no_show_is_final(self):
        with pytest.raises(InvalidStatusTransition):
            validate_status_transition(AppointmentStatus.no_show, AppointmentStatus.confirmed)

    def test_pending_cannot_go_to_in_progress(self):
        with pytest.raises(InvalidStatusTransition):
            validate_status_transition(
                AppointmentStatus.pending_approval, AppointmentStatus.in_progress
            )

    def test_pending_cannot_go_to_completed(self):
        with pytest.raises(InvalidStatusTransition):
            validate_status_transition(
                AppointmentStatus.pending_approval, AppointmentStatus.completed
            )

    def test_in_progress_cannot_go_to_confirmed(self):
        with pytest.raises(InvalidStatusTransition):
            validate_status_transition(
                AppointmentStatus.in_progress, AppointmentStatus.confirmed
            )
