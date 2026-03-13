import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import select, func

from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.payment import Payment, PartialPaymentRecord
from app.domain.enums import PaymentStatus


class PaymentRepository(BaseRepository[Payment]):
    def _base_query(self, professional_id: uuid.UUID):
        return select(Payment).where(Payment.professional_id == professional_id)

    def list(
        self,
        professional_id: uuid.UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[Payment]:
        stmt = self._base_query(professional_id)
        if from_date:
            stmt = stmt.where(Payment.paid_at >= from_date)
        if to_date:
            stmt = stmt.where(Payment.paid_at <= to_date)
        return list(self.session.exec(stmt.order_by(Payment.created_at.desc())).all())

    def get_by_id(self, professional_id: uuid.UUID, payment_id: uuid.UUID) -> Optional[Payment]:
        return self.session.exec(
            self._base_query(professional_id).where(Payment.id == payment_id)
        ).first()

    def get_by_appointment(
        self, professional_id: uuid.UUID, appointment_id: uuid.UUID
    ) -> Optional[Payment]:
        return self.session.exec(
            self._base_query(professional_id).where(
                Payment.appointment_id == appointment_id
            )
        ).first()

    def get_partial_records(self, payment_id: uuid.UUID) -> List[PartialPaymentRecord]:
        return list(
            self.session.exec(
                select(PartialPaymentRecord).where(
                    PartialPaymentRecord.payment_id == payment_id
                )
            ).all()
        )

    def create(self, payment: Payment) -> Payment:
        return self._save(payment)

    def update(self, payment: Payment) -> Payment:
        return self._touch(payment)

    def add_partial(self, partial: PartialPaymentRecord) -> PartialPaymentRecord:
        self.session.add(partial)
        self.session.commit()
        self.session.refresh(partial)
        return partial

    def delete(self, payment: Payment) -> None:
        self._delete(payment)

    # --- Cash flow with joins ---

    def get_cash_flow(
        self,
        professional_id: uuid.UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[tuple]:
        """Returns list of (Payment, client_name, procedure_name) tuples."""
        from app.domain.entities.client import Client
        from app.domain.entities.appointment import Appointment
        from app.domain.entities.procedure import Procedure

        stmt = (
            select(
                Payment,
                Client.name.label("client_name"),
                Procedure.name.label("procedure_name"),
            )
            .outerjoin(Client, Payment.client_id == Client.id)
            .outerjoin(Appointment, Payment.appointment_id == Appointment.id)
            .outerjoin(Procedure, Appointment.procedure_id == Procedure.id)
            .where(Payment.professional_id == professional_id)
        )
        if from_date:
            stmt = stmt.where(Payment.created_at >= from_date)
        if to_date:
            stmt = stmt.where(Payment.created_at <= to_date)
        stmt = stmt.order_by(Payment.created_at.desc())
        rows = self.session.execute(stmt).all()
        return [(row[0], row[1], row[2]) for row in rows]

    # --- Stats queries ---

    def get_stats(self, professional_id: uuid.UUID) -> dict:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

        # Week start (Monday)
        week_start = today_start - __import__("datetime").timedelta(days=now.weekday())
        # Month start
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        # Last month
        if now.month == 1:
            last_month_start = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
            last_month_end = month_start
        else:
            last_month_start = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
            last_month_end = month_start

        def _sum(from_dt, to_dt):
            result = self.session.exec(
                select(func.coalesce(func.sum(Payment.paid_amount_in_cents), 0)).where(
                    Payment.professional_id == professional_id,
                    Payment.status == PaymentStatus.paid,
                    Payment.paid_at >= from_dt,
                    Payment.paid_at < to_dt,
                )
            ).one()
            return result or 0

        today = _sum(today_start, today_start.replace(hour=23, minute=59, second=59))
        this_week = _sum(week_start, now)
        this_month = _sum(month_start, now)
        last_month = _sum(last_month_start, last_month_end)

        growth = 0.0
        if last_month > 0:
            growth = round((this_month - last_month) / last_month * 100, 1)

        return {
            "today_in_cents": today,
            "this_week_in_cents": this_week,
            "this_month_in_cents": this_month,
            "last_month_in_cents": last_month,
            "growth_percent": growth,
        }

    def get_monthly_revenue(self, professional_id: uuid.UUID, months: int = 6) -> List[dict]:
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        results = []
        for i in range(months - 1, -1, -1):
            if now.month - i <= 0:
                year = now.year - 1
                month = 12 + (now.month - i)
            else:
                year = now.year
                month = now.month - i
            start = datetime(year, month, 1, tzinfo=timezone.utc)
            if month == 12:
                end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

            total = self.session.exec(
                select(func.coalesce(func.sum(Payment.paid_amount_in_cents), 0)).where(
                    Payment.professional_id == professional_id,
                    Payment.status == PaymentStatus.paid,
                    Payment.paid_at >= start,
                    Payment.paid_at < end,
                )
            ).one() or 0

            results.append({"month": f"{year:04d}-{month:02d}", "amount_in_cents": total})
        return results

    def get_method_breakdown(
        self,
        professional_id: uuid.UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict:
        from app.domain.enums import PaymentMethod
        stmt = select(Payment.method, func.sum(Payment.paid_amount_in_cents)).where(
            Payment.professional_id == professional_id,
            Payment.status == PaymentStatus.paid,
        )
        if from_date:
            stmt = stmt.where(Payment.paid_at >= from_date)
        if to_date:
            stmt = stmt.where(Payment.paid_at <= to_date)
        stmt = stmt.group_by(Payment.method)

        rows = self.session.exec(stmt).all()
        breakdown = {m.value: 0 for m in PaymentMethod}
        for method, total in rows:
            if method:
                breakdown[method.value if hasattr(method, "value") else method] = total or 0
        return breakdown
