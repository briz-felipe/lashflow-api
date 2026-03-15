import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import select, func, col
from sqlalchemy import and_

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.client import Client
from app.domain.entities.appointment import Appointment
from app.domain.entities.payment import Payment
from app.domain.entities.procedure import Procedure
from app.domain.enums import AppointmentStatus


class ClientWithStats:
    def __init__(
        self,
        client: Client,
        total_spent: int,
        appointments_count: int,
        last_appointment_date: Optional[datetime],
    ):
        # Expose all client fields
        for attr in vars(client):
            if not attr.startswith("_"):
                setattr(self, attr, getattr(client, attr))
        self.total_spent = total_spent
        self.appointments_count = appointments_count
        self.last_appointment_date = last_appointment_date
        # Keep the original entity accessible
        self._client = client


class ClientRepository(BaseRepository[Client]):
    def _base_query(self, professional_id: uuid.UUID):
        return select(Client).where(
            Client.professional_id == professional_id,
            Client.deleted_at == None,  # noqa: E711
        )

    def list(
        self,
        professional_id: uuid.UUID,
        search: Optional[str] = None,
        segments: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[List[Client], int]:
        stmt = self._base_query(professional_id)

        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                (Client.name.ilike(term))
                | (Client.phone.ilike(term))
                | (Client.email.ilike(term))
            )

        total = self.session.exec(
            select(func.count()).select_from(stmt.subquery())
        ).one()

        offset = (page - 1) * per_page
        clients = self.session.exec(stmt.offset(offset).limit(per_page)).all()
        return list(clients), total

    def get_by_id(self, professional_id: uuid.UUID, client_id: uuid.UUID) -> Optional[Client]:
        # NOTE: Cache hook — cache by (professional_id, client_id)
        return self.session.exec(
            self._base_query(professional_id).where(Client.id == client_id)
        ).first()

    def get_by_phone(self, professional_id: uuid.UUID, phone: str) -> Optional[Client]:
        return self.session.exec(
            self._base_query(professional_id).where(Client.phone == phone)
        ).first()

    def search(self, professional_id: uuid.UUID, q: str) -> List[Client]:
        term = f"%{q}%"
        return list(
            self.session.exec(
                self._base_query(professional_id).where(
                    (Client.name.ilike(term))
                    | (Client.phone.ilike(term))
                    | (Client.email.ilike(term))
                ).limit(20)
            ).all()
        )

    def create(self, client: Client) -> Client:
        return self._save(client)

    def update(self, client: Client) -> Client:
        return self._touch(client)

    def soft_delete(self, client: Client) -> None:
        client.deleted_at = datetime.now(timezone.utc)
        self._touch(client)

    def get_stats(
        self, professional_id: uuid.UUID, client_id: uuid.UUID
    ) -> tuple[int, int, Optional[datetime], Optional[str]]:
        """Returns (total_spent, appointments_count, last_appointment_date, most_used_procedure_name)."""
        # Count completed appointments and get last date
        appt_result = self.session.exec(
            select(
                func.count(Appointment.id),
                func.max(Appointment.scheduled_at),
            ).where(
                Appointment.professional_id == professional_id,
                Appointment.client_id == client_id,
                Appointment.status == AppointmentStatus.completed,
            )
        ).one()
        appointments_count = appt_result[0] or 0
        last_appointment_date = appt_result[1]

        # Sum paid amounts
        payment_result = self.session.exec(
            select(func.coalesce(func.sum(Payment.paid_amount_in_cents), 0)).where(
                Payment.professional_id == professional_id,
                Payment.client_id == client_id,
            )
        ).one()
        total_spent = payment_result or 0

        # Most used procedure name among completed appointments
        name_result = self.session.exec(
            select(Procedure.name, func.count(Appointment.id).label("cnt"))
            .where(
                Appointment.professional_id == professional_id,
                Appointment.client_id == client_id,
                Appointment.status == AppointmentStatus.completed,
                Appointment.procedure_id == Procedure.id,
            )
            .group_by(Procedure.name)
            .order_by(func.count(Appointment.id).desc())
            .limit(1)
        ).first()
        most_used_procedure_name = name_result[0] if name_result else None

        return total_spent, appointments_count, last_appointment_date, most_used_procedure_name
