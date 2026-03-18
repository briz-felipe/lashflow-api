import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session, select
from app.domain.entities.professional_settings import ProfessionalSettings

DEFAULT_SEGMENT_RULES = {
    "vipMinAppointments": 5,
    "vipMinSpentCents": 100_000,
    "recorrenteMaxDays": 45,
    "recorrenteMinAppointments": 2,
    "inativaMinDays": 60,
}


class ProfessionalSettingsRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_segment_rules(self, professional_id: uuid.UUID) -> dict:
        settings = self.session.exec(
            select(ProfessionalSettings).where(
                ProfessionalSettings.professional_id == professional_id
            )
        ).first()
        if settings is None or settings.segment_rules is None:
            return DEFAULT_SEGMENT_RULES.copy()
        return {**DEFAULT_SEGMENT_RULES, **settings.segment_rules}

    def save_segment_rules(self, professional_id: uuid.UUID, rules: dict) -> dict:
        settings = self.session.exec(
            select(ProfessionalSettings).where(
                ProfessionalSettings.professional_id == professional_id
            )
        ).first()
        if settings is None:
            settings = ProfessionalSettings(
                professional_id=professional_id,
                segment_rules=rules,
                updated_at=datetime.now(timezone.utc),
            )
            self.session.add(settings)
        else:
            settings.segment_rules = rules
            settings.updated_at = datetime.now(timezone.utc)
            self.session.add(settings)
        self.session.commit()
        self.session.refresh(settings)
        return {**DEFAULT_SEGMENT_RULES, **settings.segment_rules}
