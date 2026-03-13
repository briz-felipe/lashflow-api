import uuid
from typing import List
from app.interface.schemas.base import CamelModel


class TimeSlotItem(CamelModel):
    day_of_week: int
    start_time: str
    end_time: str
    is_available: bool


class TimeSlotResponse(CamelModel):
    id: uuid.UUID
    day_of_week: int
    start_time: str
    end_time: str
    is_available: bool


class TimeSlotsUpdate(CamelModel):
    slots: List[TimeSlotItem]
