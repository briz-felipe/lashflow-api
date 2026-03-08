import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from app.domain.enums import AnamnesisHairLoss, AnamnosisProcedureType


class Anamnesis(SQLModel, table=True):
    __tablename__ = "anamneses"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    professional_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)

    # Health fields
    has_allergy: bool = Field(default=False)
    allergy_details: Optional[str] = Field(default=None)
    had_eye_surgery_last_3_months: bool = Field(default=False)
    has_eye_disease: bool = Field(default=False)
    eye_disease_details: Optional[str] = Field(default=None)
    uses_eye_drops: bool = Field(default=False)
    family_thyroid_history: bool = Field(default=False)
    has_glaucoma: bool = Field(default=False)
    hair_loss_grade: Optional[AnamnesisHairLoss] = Field(default=None)
    prone_to_blepharitis: bool = Field(default=False)
    has_epilepsy: bool = Field(default=False)

    # Service
    procedure_type: AnamnosisProcedureType
    mapping: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # LashMapping

    # Authorizations
    authorized_photo_publishing: bool = Field(default=False)
    signed_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
