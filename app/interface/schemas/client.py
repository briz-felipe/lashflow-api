import uuid
from datetime import datetime
from typing import Optional, List
from app.interface.schemas.base import CamelModel
from app.domain.enums import ClientSegment


class AddressSchema(CamelModel):
    street: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class ClientCreate(CamelModel):
    name: str
    phone: str
    email: Optional[str] = None
    instagram: Optional[str] = None
    birthday: Optional[str] = None
    notes: Optional[str] = None
    address: Optional[AddressSchema] = None


class ClientUpdate(CamelModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    instagram: Optional[str] = None
    birthday: Optional[str] = None
    notes: Optional[str] = None
    address: Optional[AddressSchema] = None
    segments: Optional[List[ClientSegment]] = None


class ClientResponse(CamelModel):
    id: uuid.UUID
    name: str
    phone: str
    email: Optional[str]
    instagram: Optional[str]
    birthday: Optional[str]
    notes: Optional[str]
    address: Optional[dict]
    segments: list
    favorite_procedure_id: Optional[uuid.UUID]
    # Computed fields (populated from stats query)
    total_spent: int = 0
    appointments_count: int = 0
    last_appointment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
