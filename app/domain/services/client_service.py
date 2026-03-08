import re
from datetime import datetime, timezone
from app.domain.enums import ClientSegment, LashTechnique
from typing import Optional, List

def normalize_phone(phone: str) -> str:
    """Strip all non-digit characters from a phone number."""
    return re.sub(r"\D", "", phone)


def calculate_segments(
    appointments_count: int,
    total_spent_cents: int,
    last_appointment_date: Optional[datetime],
    most_used_technique: Optional[LashTechnique],
    now: Optional[datetime] = None,
) -> List[ClientSegment]:
    """
    Calculates all applicable segments for a client.
    A client can have multiple segments simultaneously.

    Rules (from readme section 4.7):
    - vip:        appointments_count >= 5 OR total_spent >= R$1000 (100000 cents)
    - recorrente: last appointment < 45 days ago AND appointments_count >= 2
    - inativa:    last appointment > 60 days ago (or never had a completed appointment)
    - volume:     most used technique is 'volume' or 'mega_volume'
    - classic:    most used technique is 'classic'
    - hybrid:     most used technique is 'hybrid'
    """
    now = now or datetime.now(timezone.utc)
    segments: List[ClientSegment] = []

    # VIP
    if appointments_count >= 5 or total_spent_cents >= 100_000:
        segments.append(ClientSegment.vip)

    # Recorrente / Inativa
    if last_appointment_date is not None:
        # Make timezone-aware for comparison
        last = last_appointment_date
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        delta_days = (now - last).days

        if delta_days < 45 and appointments_count >= 2:
            segments.append(ClientSegment.recorrente)
        if delta_days > 60:
            segments.append(ClientSegment.inativa)
    else:
        # Never had a completed appointment
        segments.append(ClientSegment.inativa)

    # Technique-based segments
    if most_used_technique in (LashTechnique.volume, LashTechnique.mega_volume):
        segments.append(ClientSegment.volume)
    elif most_used_technique == LashTechnique.classic:
        segments.append(ClientSegment.classic)
    elif most_used_technique == LashTechnique.hybrid:
        segments.append(ClientSegment.hybrid)

    return segments
