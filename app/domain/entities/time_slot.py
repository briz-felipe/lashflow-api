import uuid
from sqlmodel import SQLModel, Field


class TimeSlot(SQLModel, table=True):
    __tablename__ = "time_slots"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    day_of_week: int = Field(ge=0, le=6)  # 0=Sunday
    start_time: str = Field(max_length=5)  # "HH:MM"
    end_time: str = Field(max_length=5)    # "HH:MM"
    is_available: bool = Field(default=True)
