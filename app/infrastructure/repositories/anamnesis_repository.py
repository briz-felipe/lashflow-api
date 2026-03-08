import uuid
from typing import Optional, List
from sqlmodel import select

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.anamnesis import Anamnesis


class AnamnesisRepository(BaseRepository[Anamnesis]):
    def _base_query(self, professional_id: uuid.UUID):
        return select(Anamnesis).where(Anamnesis.professional_id == professional_id)

    def list_by_client(
        self, professional_id: uuid.UUID, client_id: uuid.UUID
    ) -> List[Anamnesis]:
        return list(
            self.session.exec(
                self._base_query(professional_id)
                .where(Anamnesis.client_id == client_id)
                .order_by(Anamnesis.created_at.desc())
            ).all()
        )

    def get_by_id(
        self, professional_id: uuid.UUID, anamnesis_id: uuid.UUID
    ) -> Optional[Anamnesis]:
        return self.session.exec(
            self._base_query(professional_id).where(Anamnesis.id == anamnesis_id)
        ).first()

    def create(self, anamnesis: Anamnesis) -> Anamnesis:
        return self._save(anamnesis)

    def update(self, anamnesis: Anamnesis) -> Anamnesis:
        return self._touch(anamnesis)

    def delete(self, anamnesis: Anamnesis) -> None:
        self._delete(anamnesis)
