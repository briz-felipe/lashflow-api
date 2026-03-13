import uuid
from datetime import datetime
from typing import Optional
from pydantic import model_validator
from app.domain.enums import AnamnesisHairLoss, AnamnosisProcedureType
from app.domain.exceptions import AllergyDetailRequired
from app.interface.schemas.base import CamelModel


class LashMappingSchema(CamelModel):
    size: Optional[str] = None
    curve: Optional[str] = None
    thickness: Optional[str] = None


class AnamnesisCreate(CamelModel):
    client_id: uuid.UUID
    has_allergy: bool = False
    allergy_details: Optional[str] = None
    had_eye_surgery_last_3_months: bool = False
    has_eye_disease: bool = False
    eye_disease_details: Optional[str] = None
    uses_eye_drops: bool = False
    family_thyroid_history: bool = False
    has_glaucoma: bool = False
    hair_loss_grade: Optional[AnamnesisHairLoss] = None
    prone_to_blepharitis: bool = False
    has_epilepsy: bool = False
    procedure_type: AnamnosisProcedureType
    mapping: Optional[LashMappingSchema] = None
    authorized_photo_publishing: bool = False
    signed_at: Optional[datetime] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def allergy_detail_required(self) -> "AnamnesisCreate":
        if self.has_allergy and not self.allergy_details:
            raise ValueError("allergy_details is required when has_allergy is True")
        return self


class AnamnesisUpdate(CamelModel):
    has_allergy: Optional[bool] = None
    allergy_details: Optional[str] = None
    had_eye_surgery_last_3_months: Optional[bool] = None
    has_eye_disease: Optional[bool] = None
    eye_disease_details: Optional[str] = None
    uses_eye_drops: Optional[bool] = None
    family_thyroid_history: Optional[bool] = None
    has_glaucoma: Optional[bool] = None
    hair_loss_grade: Optional[AnamnesisHairLoss] = None
    prone_to_blepharitis: Optional[bool] = None
    has_epilepsy: Optional[bool] = None
    procedure_type: Optional[AnamnosisProcedureType] = None
    mapping: Optional[LashMappingSchema] = None
    authorized_photo_publishing: Optional[bool] = None
    signed_at: Optional[datetime] = None
    notes: Optional[str] = None


class AnamnesisResponse(CamelModel):
    id: uuid.UUID
    client_id: uuid.UUID
    has_allergy: bool
    allergy_details: Optional[str]
    had_eye_surgery_last_3_months: bool
    has_eye_disease: bool
    eye_disease_details: Optional[str]
    uses_eye_drops: bool
    family_thyroid_history: bool
    has_glaucoma: bool
    hair_loss_grade: Optional[AnamnesisHairLoss]
    prone_to_blepharitis: bool
    has_epilepsy: bool
    procedure_type: AnamnosisProcedureType
    mapping: Optional[dict]
    authorized_photo_publishing: bool
    signed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
