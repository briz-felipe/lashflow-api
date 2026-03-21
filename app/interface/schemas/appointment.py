import uuid
from datetime import datetime
from typing import Optional, List
from app.interface.schemas.base import CamelModel
from app.domain.enums import AppointmentStatus, LashServiceType, CancelledBy


class AppointmentProcedureInput(CamelModel):
    procedure_id: uuid.UUID
    custom_price_in_cents: Optional[int] = None  # null = use table price


class AppointmentProcedureResponse(CamelModel):
    id: uuid.UUID
    procedure_id: uuid.UUID
    procedure_name: str
    custom_price_in_cents: Optional[int] = None
    original_price_in_cents: int
    effective_price_in_cents: int
    duration_minutes: int


class AppointmentCreate(CamelModel):
    client_id: uuid.UUID
    procedure_id: Optional[uuid.UUID] = None  # legacy single-procedure (used if procedures is empty)
    scheduled_at: datetime
    service_type: Optional[LashServiceType] = None
    price_charged: Optional[int] = None       # legacy: defaults to procedure.price_in_cents if omitted
    duration_minutes: Optional[int] = None    # legacy: override when combining multiple procedures
    procedure_name: Optional[str] = None      # legacy: override for combined name
    notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None  # if omitted, defaults to pending_approval
    procedures: Optional[List[AppointmentProcedureInput]] = None  # new multi-procedure


class AppointmentStatusUpdate(CamelModel):
    status: AppointmentStatus


class AppointmentCancelRequest(CamelModel):
    reason: Optional[str] = None
    cancelled_by: Optional[CancelledBy] = None


class AppointmentUpdate(CamelModel):
    procedure_id: Optional[uuid.UUID] = None
    scheduled_at: Optional[datetime] = None
    service_type: Optional[LashServiceType] = None
    price_charged: Optional[int] = None
    duration_minutes: Optional[int] = None
    procedure_name: Optional[str] = None  # empty string = clear override
    notes: Optional[str] = None
    procedures: Optional[List[AppointmentProcedureInput]] = None  # new multi-procedure


class AppointmentResponse(CamelModel):
    id: uuid.UUID
    client_id: uuid.UUID
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    procedure_id: uuid.UUID
    procedure_name: Optional[str] = None
    payment_id: Optional[uuid.UUID]
    service_type: Optional[LashServiceType]
    status: AppointmentStatus
    scheduled_at: datetime
    duration_minutes: int
    ends_at: datetime
    price_charged: int
    notes: Optional[str]
    requested_at: datetime
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    cancelled_by: Optional[CancelledBy]
    created_at: datetime
    updated_at: datetime
    procedures: List[AppointmentProcedureResponse] = []


class AvailableSlotsResponse(CamelModel):
    slots: List[str]


class AvailableDatesResponse(CamelModel):
    dates: List[str]  # "YYYY-MM-DD"
