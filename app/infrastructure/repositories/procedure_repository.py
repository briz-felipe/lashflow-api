import uuid
from typing import Optional, List
from sqlmodel import select, func

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.procedure import Procedure


class ProcedureRepository(BaseRepository[Procedure]):
    def _base_query(self, professional_id: uuid.UUID):
        return select(Procedure).where(Procedure.professional_id == professional_id)

    def list(
        self,
        professional_id: uuid.UUID,
        active_only: bool = False,
    ) -> List[Procedure]:
        stmt = self._base_query(professional_id)
        if active_only:
            stmt = stmt.where(Procedure.is_active == True)  # noqa: E712
        return list(self.session.exec(stmt).all())

    def get_by_id(self, professional_id: uuid.UUID, procedure_id: uuid.UUID) -> Optional[Procedure]:
        # NOTE: Cache hook — cache by (professional_id, procedure_id)
        return self.session.exec(
            self._base_query(professional_id).where(Procedure.id == procedure_id)
        ).first()

    def create(self, procedure: Procedure) -> Procedure:
        return self._save(procedure)

    def update(self, procedure: Procedure) -> Procedure:
        return self._touch(procedure)

    def delete(self, procedure: Procedure) -> None:
        self._delete(procedure)

    def toggle_active(self, procedure: Procedure) -> Procedure:
        procedure.is_active = not procedure.is_active
        return self._touch(procedure)
