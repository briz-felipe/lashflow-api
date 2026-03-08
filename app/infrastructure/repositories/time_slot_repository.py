import uuid
from typing import Optional, List
from sqlmodel import select

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.time_slot import TimeSlot


class TimeSlotRepository(BaseRepository[TimeSlot]):
    def list(self, professional_id: uuid.UUID) -> List[TimeSlot]:
        return list(
            self.session.exec(
                select(TimeSlot)
                .where(TimeSlot.professional_id == professional_id)
                .order_by(TimeSlot.day_of_week)
            ).all()
        )

    def get_for_day(self, professional_id: uuid.UUID, day_of_week: int) -> Optional[TimeSlot]:
        """Returns the time slot for a given day of week (0=Sunday)."""
        return self.session.exec(
            select(TimeSlot).where(
                TimeSlot.professional_id == professional_id,
                TimeSlot.day_of_week == day_of_week,
            )
        ).first()

    def upsert_many(self, professional_id: uuid.UUID, slots: List[TimeSlot]) -> List[TimeSlot]:
        """Replace all time slots for a professional."""
        existing = self.list(professional_id)
        for slot in existing:
            self.session.delete(slot)
        for slot in slots:
            self.session.add(slot)
        self.session.commit()
        for slot in slots:
            self.session.refresh(slot)
        return slots
