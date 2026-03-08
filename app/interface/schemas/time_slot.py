import uuid
from pydantic import BaseModel
from typing import List

class TimeSlotItem(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    is_available: bool


class TimeSlotResponse(BaseModel):
    id: uuid.UUID
    day_of_week: int
    start_time: str
    end_time: str
    is_available: bool

    model_config = {"from_attributes": True}


class TimeSlotsUpdate(BaseModel):
    slots: List[TimeSlotItem]
