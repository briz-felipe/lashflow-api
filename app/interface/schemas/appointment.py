import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.domain.enums import AppointmentStatus, LashServiceType, CancelledBy


class AppointmentCreate(BaseModel):
    client_id: uuid.UUID
    procedure_id: uuid.UUID
    scheduled_at: datetime
    service_type: Optional[LashServiceType] = None
    price_charged: int
    notes: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentCancelRequest(BaseModel):
    reason: Optional[str] = None
    cancelled_by: Optional[CancelledBy] = None


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    procedure_id: uuid.UUID
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

    model_config = {"from_attributes": True}


class AvailableSlotsResponse(BaseModel):
    slots: List[str]
