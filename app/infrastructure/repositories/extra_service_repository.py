import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import Session, select

from app.domain.entities.extra_service import ExtraService


class ExtraServiceRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self, professional_id: uuid.UUID, include_inactive: bool = False) -> List[ExtraService]:
        stmt = select(ExtraService).where(ExtraService.professional_id == professional_id)
        if not include_inactive:
            stmt = stmt.where(ExtraService.is_active == True)
        stmt = stmt.order_by(ExtraService.name)
        return list(self.session.exec(stmt).all())

    def get_by_id(self, professional_id: uuid.UUID, extra_id: uuid.UUID) -> Optional[ExtraService]:
        stmt = (
            select(ExtraService)
            .where(ExtraService.professional_id == professional_id)
            .where(ExtraService.id == extra_id)
        )
        return self.session.exec(stmt).first()

    def create(self, extra: ExtraService) -> ExtraService:
        self.session.add(extra)
        self.session.commit()
        self.session.refresh(extra)
        return extra

    def update(self, extra: ExtraService) -> ExtraService:
        extra.updated_at = datetime.now(timezone.utc)
        self.session.add(extra)
        self.session.commit()
        self.session.refresh(extra)
        return extra

    def delete(self, extra: ExtraService) -> None:
        self.session.delete(extra)
        self.session.commit()
