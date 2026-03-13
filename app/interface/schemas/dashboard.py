from typing import List
from app.interface.schemas.base import CamelModel
from app.interface.schemas.payment import PaymentStatsResponse, MonthlyRevenueItem
from app.interface.schemas.appointment import AppointmentResponse


class DashboardStatsResponse(CamelModel):
    total_clients: int
    clients_with_upcoming_appointments: int
    today_appointments_count: int
    revenue_stats: PaymentStatsResponse
    monthly_revenue: List[MonthlyRevenueItem]
    pending_approvals_count: int


class DashboardTodayResponse(CamelModel):
    appointments: List[AppointmentResponse]
    pending_approvals_count: int
