import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func

from app.infrastructure.database import get_session
from app.infrastructure.repositories.payment_repository import PaymentRepository
from app.infrastructure.repositories.appointment_repository import AppointmentRepository
from app.infrastructure.repositories.client_repository import ClientRepository
from app.domain.entities.appointment import Appointment
from app.domain.entities.client import Client
from app.domain.enums import AppointmentStatus
from app.interface.dependencies import get_professional_id
from app.interface.schemas.dashboard import DashboardStatsResponse, DashboardTodayResponse
from app.interface.schemas.payment import PaymentStatsResponse, MonthlyRevenueItem
from app.interface.schemas.appointment import AppointmentResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def dashboard_stats(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    payment_repo = PaymentRepository(session)
    appt_repo = AppointmentRepository(session)

    now = datetime.now(timezone.utc)

    # Total clients (non-deleted)
    total_clients = session.exec(
        select(func.count(Client.id)).where(
            Client.professional_id == professional_id,
            Client.deleted_at == None,  # noqa: E711
        )
    ).one() or 0

    # Clients with upcoming appointments
    clients_with_upcoming = session.exec(
        select(func.count(func.distinct(Appointment.client_id))).where(
            Appointment.professional_id == professional_id,
            Appointment.scheduled_at >= now,
            Appointment.status.in_([AppointmentStatus.confirmed, AppointmentStatus.pending_approval]),
        )
    ).one() or 0

    today_appointments = appt_repo.get_today(professional_id)
    pending_count = len(appt_repo.get_pending_approvals(professional_id))

    revenue_stats = payment_repo.get_stats(professional_id)
    monthly_revenue = payment_repo.get_monthly_revenue(professional_id, months=6)

    return DashboardStatsResponse(
        total_clients=total_clients,
        clients_with_upcoming_appointments=clients_with_upcoming,
        today_appointments_count=len(today_appointments),
        revenue_stats=PaymentStatsResponse(**revenue_stats),
        monthly_revenue=[MonthlyRevenueItem(**m) for m in monthly_revenue],
        pending_approvals_count=pending_count,
    )


@router.get("/today", response_model=DashboardTodayResponse)
def dashboard_today(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    appt_repo = AppointmentRepository(session)
    today = appt_repo.get_today(professional_id)
    pending_count = len(appt_repo.get_pending_approvals(professional_id))

    return DashboardTodayResponse(
        appointments=[
            AppointmentResponse.model_validate(a) | {"ends_at": a.ends_at}
            for a in today
        ],
        pending_approvals_count=pending_count,
    )
