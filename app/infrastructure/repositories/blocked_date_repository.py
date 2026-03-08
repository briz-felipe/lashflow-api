import uuid
from typing import Optional, List
from sqlmodel import select

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.blocked_date import BlockedDate


class BlockedDateRepository(BaseRepository[BlockedDate]):
    def list(self, professional_id: uuid.UUID) -> List[BlockedDate]:
        return list(
            self.session.exec(
                select(BlockedDate)
                .where(BlockedDate.professional_id == professional_id)
                .order_by(BlockedDate.date)
            ).all()
        )

    def get_by_id(
        self, professional_id: uuid.UUID, blocked_date_id: uuid.UUID
    ) -> Optional[BlockedDate]:
        return self.session.exec(
            select(BlockedDate).where(
                BlockedDate.professional_id == professional_id,
                BlockedDate.id == blocked_date_id,
            )
        ).first()

    def create(self, blocked_date: BlockedDate) -> BlockedDate:
        return self._save(blocked_date)

    def delete(self, blocked_date: BlockedDate) -> None:
        self._delete(blocked_date)
