import re
from datetime import datetime, timezone
from app.domain.enums import ClientSegment
from typing import Optional, List


def normalize_phone(phone: str) -> str:
    """Strip all non-digit characters from a phone number."""
    return re.sub(r"\D", "", phone)


def _segment_from_procedure_name(name: Optional[str]) -> Optional[ClientSegment]:
    """Derive a technique segment from a procedure name using keyword matching."""
    if not name:
        return None
    lower = name.lower()
    if "mega" in lower and "volume" in lower:
        return ClientSegment.volume
    if "volume" in lower:
        return ClientSegment.volume
    if "classic" in lower or "clássico" in lower or "classico" in lower:
        return ClientSegment.classic
    if "hybrid" in lower or "híbrido" in lower or "hibrido" in lower:
        return ClientSegment.hybrid
    return None


def calculate_segments(
    appointments_count: int,
    total_spent_cents: int,
    last_appointment_date: Optional[datetime],
    most_used_procedure_name: Optional[str] = None,
    now: Optional[datetime] = None,
    vip_min_appointments: int = 5,
    vip_min_spent_cents: int = 100_000,
    recorrente_max_days: int = 45,
    recorrente_min_appointments: int = 2,
    inativa_min_days: int = 60,
) -> List[ClientSegment]:
    """
    Calculates all applicable segments for a client.
    A client can have multiple segments simultaneously.

    Rules (configurable thresholds):
    - vip:        appointments_count >= vip_min_appointments OR total_spent >= vip_min_spent_cents
    - recorrente: last appointment < recorrente_max_days ago AND appointments_count >= recorrente_min_appointments
    - inativa:    last appointment > inativa_min_days ago (or never had a completed appointment)
    - volume:     most used procedure name contains 'volume' or 'mega volume'
    - classic:    most used procedure name contains 'classic'
    - hybrid:     most used procedure name contains 'hybrid'
    """
    now = now or datetime.now(timezone.utc)
    segments: List[ClientSegment] = []

    # VIP
    if appointments_count >= vip_min_appointments or total_spent_cents >= vip_min_spent_cents:
        segments.append(ClientSegment.vip)

    # Recorrente / Inativa
    if last_appointment_date is not None:
        last = last_appointment_date
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        delta_days = (now - last).days

        if delta_days < recorrente_max_days and appointments_count >= recorrente_min_appointments:
            segments.append(ClientSegment.recorrente)
        if delta_days > inativa_min_days:
            segments.append(ClientSegment.inativa)
    else:
        segments.append(ClientSegment.inativa)

    # Technique-based segments derived from most used procedure name
    technique_segment = _segment_from_procedure_name(most_used_procedure_name)
    if technique_segment:
        segments.append(technique_segment)

    return segments
