import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.infrastructure.database import get_session
from app.infrastructure.repositories.time_slot_repository import TimeSlotRepository
from app.infrastructure.repositories.blocked_date_repository import BlockedDateRepository
from app.infrastructure.repositories.whatsapp_template_repository import WhatsAppTemplateRepository
from app.domain.entities.time_slot import TimeSlot
from app.domain.entities.blocked_date import BlockedDate
from app.domain.entities.whatsapp_template import WhatsAppTemplate, _slugify
from app.interface.dependencies import get_professional_id
from app.interface.schemas.time_slot import TimeSlotResponse, TimeSlotsUpdate
from app.interface.schemas.blocked_date import BlockedDateCreate, BlockedDateResponse
from app.interface.schemas.whatsapp_template import (
    WhatsAppTemplateCreate,
    WhatsAppTemplateUpdate,
    WhatsAppTemplateResponse,
)

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


# ── WhatsApp Templates ────────────────────────────────────────────────────────

def _unique_slug(repo: WhatsAppTemplateRepository, professional_id: uuid.UUID, base: str, exclude_id=None) -> str:
    slug = base
    counter = 2
    while repo.slug_exists(professional_id, slug, exclude_id=exclude_id):
        slug = f"{base}_{counter}"
        counter += 1
    return slug


@router.get("/whatsapp-templates", response_model=List[WhatsAppTemplateResponse])
def list_whatsapp_templates(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    return WhatsAppTemplateRepository(session).list(professional_id)


@router.post("/whatsapp-templates", response_model=WhatsAppTemplateResponse, status_code=201)
def create_whatsapp_template(
    body: WhatsAppTemplateCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = WhatsAppTemplateRepository(session)
    base_slug = _slugify(body.name)
    slug = _unique_slug(repo, professional_id, base_slug)
    template = WhatsAppTemplate(
        professional_id=professional_id,
        slug=slug,
        name=body.name,
        description=body.description or "",
        message=body.message,
    )
    return repo.create(template)


@router.put("/whatsapp-templates/{template_id}", response_model=WhatsAppTemplateResponse)
def update_whatsapp_template(
    template_id: uuid.UUID,
    body: WhatsAppTemplateUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = WhatsAppTemplateRepository(session)
    template = repo.get_by_id(professional_id, template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    if body.name is not None:
        template.name = body.name
        base_slug = _slugify(body.name)
        template.slug = _unique_slug(repo, professional_id, base_slug, exclude_id=template_id)
    if body.description is not None:
        template.description = body.description
    if body.message is not None:
        template.message = body.message
    return repo.update(template)


@router.delete("/whatsapp-templates/{template_id}", status_code=204)
def delete_whatsapp_template(
    template_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = WhatsAppTemplateRepository(session)
    template = repo.get_by_id(professional_id, template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    repo.delete(template)
