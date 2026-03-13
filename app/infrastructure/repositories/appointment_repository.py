import uuid
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional
from sqlmodel import select, func

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.appointment import Appointment
from app.domain.enums import AppointmentStatus


_ACTIVE_STATUSES = [
    AppointmentStatus.pending_approval,
    AppointmentStatus.confirmed,
    AppointmentStatus.in_progress,
]


class AppointmentRepository(BaseRepository[Appointment]):
    def _base_query(self, professional_id: uuid.UUID):
        return select(Appointment).where(Appointment.professional_id == professional_id)

    def list(
        self,
        professional_id: uuid.UUID,
        client_id: Optional[uuid.UUID] = None,
        statuses: Optional[List[AppointmentStatus]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[Appointment]:
        stmt = self._base_query(professional_id)
        if client_id:
            stmt = stmt.where(Appointment.client_id == client_id)
        if statuses:
            stmt = stmt.where(Appointment.status.in_(statuses))
        if from_date:
            stmt = stmt.where(Appointment.scheduled_at >= from_date)
        if to_date:
            stmt = stmt.where(Appointment.scheduled_at <= to_date)
        return list(self.session.exec(stmt.order_by(Appointment.scheduled_at)).all())

    def get_by_id(self, professional_id: uuid.UUID, appointment_id: uuid.UUID) -> Optional[Appointment]:
        return self.session.exec(
            self._base_query(professional_id).where(Appointment.id == appointment_id)
        ).first()

    def get_today(self, professional_id: uuid.UUID) -> List[Appointment]:
        today = datetime.now(timezone.utc).date()
        start = datetime(today.year, today.month, today.day)
        end = start + timedelta(days=1)
        return list(
            self.session.exec(
                self._base_query(professional_id)
                .where(
                    Appointment.scheduled_at >= start,
                    Appointment.scheduled_at < end,
                )
                .order_by(Appointment.scheduled_at)
            ).all()
        )

    def get_pending_approvals(self, professional_id: uuid.UUID) -> List[Appointment]:
        return list(
            self.session.exec(
                self._base_query(professional_id).where(
                    Appointment.status == AppointmentStatus.pending_approval
                )
            ).all()
        )

    def get_active_on_date(
        self, professional_id: uuid.UUID, target_date: date
    ) -> List[Appointment]:
        """Returns non-cancelled/no_show appointments on a given date (for slot conflict check)."""
        start = datetime(target_date.year, target_date.month, target_date.day)
        end = start + timedelta(days=1)
        return list(
            self.session.exec(
                self._base_query(professional_id)
                .where(
                    Appointment.scheduled_at >= start,
                    Appointment.scheduled_at < end,
                    Appointment.status.in_(_ACTIVE_STATUSES),
                )
            ).all()
        )

    def get_active_in_range(
        self, professional_id: uuid.UUID, from_date: date, to_date: date
    ) -> List[Appointment]:
        """Returns non-cancelled/no_show appointments within a date range (inclusive)."""
        start = datetime(from_date.year, from_date.month, from_date.day)
        end = datetime(to_date.year, to_date.month, to_date.day) + timedelta(days=1)
        return list(
            self.session.exec(
                self._base_query(professional_id)
                .where(
                    Appointment.scheduled_at >= start,
                    Appointment.scheduled_at < end,
                    Appointment.status.in_(_ACTIVE_STATUSES),
                )
            ).all()
        )

    def create(self, appointment: Appointment) -> Appointment:
        return self._save(appointment)

    def update(self, appointment: Appointment) -> Appointment:
        return self._touch(appointment)

    def delete(self, appointment: Appointment) -> None:
        self._delete(appointment)
