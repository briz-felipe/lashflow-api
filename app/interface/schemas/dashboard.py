from typing import List
from pydantic import BaseModel
from app.interface.schemas.payment import PaymentStatsResponse, MonthlyRevenueItem
from app.interface.schemas.appointment import AppointmentResponse


class DashboardStatsResponse(BaseModel):
    total_clients: int
    clients_with_upcoming_appointments: int
    today_appointments_count: int
    revenue_stats: PaymentStatsResponse
    monthly_revenue: List[MonthlyRevenueItem]
    pending_approvals_count: int


class DashboardTodayResponse(BaseModel):
    appointments: List[AppointmentResponse]
    pending_approvals_count: int
