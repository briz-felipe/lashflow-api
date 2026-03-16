import uuid
from typing import Optional, List
from sqlmodel import select, func

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.material import Material
from app.domain.entities.stock_movement import StockMovement


class MaterialRepository(BaseRepository[Material]):
    def _base_query(self, professional_id: uuid.UUID):
        return select(Material).where(
            Material.professional_id == professional_id,
            Material.is_active == True,  # noqa: E712
        )

    def list(
        self,
        professional_id: uuid.UUID,
        category: Optional[str] = None,
        search: Optional[str] = None,
        low_stock: bool = False,
        include_inactive: bool = False,
    ) -> List[Material]:
        stmt = select(Material).where(Material.professional_id == professional_id)
        if not include_inactive:
            stmt = stmt.where(Material.is_active == True)  # noqa: E712
        if category:
            stmt = stmt.where(Material.category == category)
        if search:
            stmt = stmt.where(Material.name.ilike(f"%{search}%"))
        if low_stock:
            stmt = stmt.where(Material.current_stock <= Material.minimum_stock)
        return list(self.session.exec(stmt).all())

    def get_by_id(
        self, professional_id: uuid.UUID, material_id: uuid.UUID
    ) -> Optional[Material]:
        # NOTE: Cache hook
        return self.session.exec(
            select(Material).where(
                Material.professional_id == professional_id,
                Material.id == material_id,
            )
        ).first()

    def create(self, material: Material) -> Material:
        return self._save(material)

    def update(self, material: Material) -> Material:
        return self._touch(material)

    def deactivate(self, material: Material) -> Material:
        material.is_active = False
        return self._touch(material)

    def get_total_stock_value(self, professional_id: uuid.UUID) -> int:
        """Returns total stock value in cents: sum(current_stock * unit_cost_in_cents)."""
        result = self.session.exec(
            select(
                func.coalesce(
                    func.sum(Material.current_stock * Material.unit_cost_in_cents), 0
                )
            ).where(
                Material.professional_id == professional_id,
                Material.is_active == True,  # noqa: E712
            )
        ).one()
        return result or 0

    def get_monthly_costs(self, professional_id: uuid.UUID, months: int = 6) -> List[dict]:
        from datetime import datetime, timezone
        from sqlmodel import col
        now = datetime.now(timezone.utc)
        results = []
        for i in range(months - 1, -1, -1):
            if now.month - i <= 0:
                year = now.year - 1
                month = 12 + (now.month - i)
            else:
                year = now.year
                month = now.month - i
            from datetime import datetime as dt_cls
            start = dt_cls(year, month, 1)
            if month == 12:
                end = dt_cls(year + 1, 1, 1)
            else:
                end = dt_cls(year, month + 1, 1)

            total = self.session.exec(
                select(func.coalesce(func.sum(StockMovement.total_cost_in_cents), 0)).where(
                    StockMovement.professional_id == professional_id,
                    StockMovement.date >= start,
                    StockMovement.date < end,
                )
            ).one() or 0

            results.append({"month": f"{year:04d}-{month:02d}", "cost_in_cents": total})
        return results
