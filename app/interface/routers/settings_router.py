import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.infrastructure.database import get_session
from app.infrastructure.repositories.time_slot_repository import TimeSlotRepository
from app.infrastructure.repositories.blocked_date_repository import BlockedDateRepository
from app.domain.entities.time_slot import TimeSlot
from app.domain.entities.blocked_date import BlockedDate
from app.interface.dependencies import get_professional_id
from app.interface.schemas.time_slot import TimeSlotResponse, TimeSlotsUpdate
from app.interface.schemas.blocked_date import BlockedDateCreate, BlockedDateResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/time-slots", response_model=List[TimeSlotResponse])
def get_time_slots(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = TimeSlotRepository(session)
    return repo.list(professional_id)


@router.put("/time-slots", response_model=List[TimeSlotResponse])
def update_time_slots(
    body: TimeSlotsUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = TimeSlotRepository(session)
    slots = [
        TimeSlot(
            professional_id=professional_id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            is_available=s.is_available,
        )
        for s in body.slots
    ]
    return repo.upsert_many(professional_id, slots)


@router.get("/blocked-dates", response_model=List[BlockedDateResponse])
def get_blocked_dates(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = BlockedDateRepository(session)
    return repo.list(professional_id)


@router.post("/blocked-dates", response_model=BlockedDateResponse, status_code=201)
def create_blocked_date(
    body: BlockedDateCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = BlockedDateRepository(session)
    blocked = BlockedDate(
        professional_id=professional_id,
        date=body.date,
        reason=body.reason,
    )
    return repo.create(blocked)


@router.delete("/blocked-dates/{blocked_date_id}", status_code=204)
def delete_blocked_date(
    blocked_date_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = BlockedDateRepository(session)
    blocked = repo.get_by_id(professional_id, blocked_date_id)
    if not blocked:
        raise HTTPException(404, "Blocked date not found")
    repo.delete(blocked)
