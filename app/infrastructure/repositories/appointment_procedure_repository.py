import uuid
from typing import List
from sqlmodel import select

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.appointment_procedure import AppointmentProcedure


class AppointmentProcedureRepository(BaseRepository[AppointmentProcedure]):

    def get_by_appointment(self, appointment_id: uuid.UUID) -> List[AppointmentProcedure]:
        stmt = select(AppointmentProcedure).where(
            AppointmentProcedure.appointment_id == appointment_id
        )
        return list(self.session.exec(stmt).all())

    def bulk_create(self, items: List[AppointmentProcedure]) -> List[AppointmentProcedure]:
        for item in items:
            self.session.add(item)
        self.session.commit()
        for item in items:
            self.session.refresh(item)
        return items

    def replace_for_appointment(
        self, appointment_id: uuid.UUID, items: List[AppointmentProcedure]
    ) -> List[AppointmentProcedure]:
        existing = self.get_by_appointment(appointment_id)
        for row in existing:
            self.session.delete(row)
        self.session.flush()
        return self.bulk_create(items)
