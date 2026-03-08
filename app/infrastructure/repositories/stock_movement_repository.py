import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import select

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.stock_movement import StockMovement
from app.domain.entities.material import Material


class StockMovementRepository(BaseRepository[StockMovement]):
    def _base_query(self, professional_id: uuid.UUID):
        return select(StockMovement).where(StockMovement.professional_id == professional_id)

    def list(
        self,
        professional_id: uuid.UUID,
        material_id: Optional[uuid.UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[StockMovement]:
        stmt = self._base_query(professional_id)
        if material_id:
            stmt = stmt.where(StockMovement.material_id == material_id)
        if from_date:
            stmt = stmt.where(StockMovement.date >= from_date)
        if to_date:
            stmt = stmt.where(StockMovement.date <= to_date)
        return list(self.session.exec(stmt.order_by(StockMovement.date.desc())).all())

    def create_with_stock_update(
        self,
        movement: StockMovement,
        material: Material,
        new_stock: int,
    ) -> StockMovement:
        """Creates the movement and updates material stock in a single transaction."""
        from datetime import datetime as dt_cls
        material.current_stock = new_stock
        material.updated_at = dt_cls.utcnow()
        self.session.add(material)
        self.session.add(movement)
        self.session.commit()
        self.session.refresh(movement)
        return movement
