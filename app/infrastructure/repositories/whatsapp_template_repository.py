import uuid
from typing import List, Optional
from sqlmodel import Session, select
from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.whatsapp_template import WhatsAppTemplate


class WhatsAppTemplateRepository(BaseRepository[WhatsAppTemplate]):
    def list(self, professional_id: uuid.UUID) -> List[WhatsAppTemplate]:
        stmt = (
            select(WhatsAppTemplate)
            .where(WhatsAppTemplate.professional_id == professional_id)
            .order_by(WhatsAppTemplate.created_at)
        )
        return list(self.session.exec(stmt).all())

    def get_by_id(self, professional_id: uuid.UUID, template_id: uuid.UUID) -> Optional[WhatsAppTemplate]:
        stmt = (
            select(WhatsAppTemplate)
            .where(WhatsAppTemplate.professional_id == professional_id)
            .where(WhatsAppTemplate.id == template_id)
        )
        return self.session.exec(stmt).first()

    def slug_exists(self, professional_id: uuid.UUID, slug: str, exclude_id: Optional[uuid.UUID] = None) -> bool:
        stmt = (
            select(WhatsAppTemplate)
            .where(WhatsAppTemplate.professional_id == professional_id)
            .where(WhatsAppTemplate.slug == slug)
        )
        if exclude_id:
            stmt = stmt.where(WhatsAppTemplate.id != exclude_id)
        return self.session.exec(stmt).first() is not None

    def create(self, template: WhatsAppTemplate) -> WhatsAppTemplate:
        return self._save(template)

    def update(self, template: WhatsAppTemplate) -> WhatsAppTemplate:
        return self._touch(template)

    def delete(self, template: WhatsAppTemplate) -> None:
        self._delete(template)
