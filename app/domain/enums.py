from enum import Enum


class AppointmentStatus(str, Enum):
    pending_approval = "pending_approval"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    partial = "partial"
    refunded = "refunded"
    failed = "failed"


class PaymentMethod(str, Enum):
    cash = "cash"
    credit_card = "credit_card"
    debit_card = "debit_card"
    pix = "pix"
    bank_transfer = "bank_transfer"
    other = "other"


class LashTechnique(str, Enum):
    classic = "classic"
    volume = "volume"
    hybrid = "hybrid"
    mega_volume = "mega_volume"
    wispy = "wispy"
    wet_look = "wet_look"
    other = "other"


class LashServiceType(str, Enum):
    application = "application"
    maintenance = "maintenance"
    removal = "removal"
    removal_application = "removal_application"
    lash_lifting = "lash_lifting"
    permanent = "permanent"


class ClientSegment(str, Enum):
    volume = "volume"
    classic = "classic"
    hybrid = "hybrid"
    vip = "vip"
    recorrente = "recorrente"
    inativa = "inativa"



class MaterialUnit(str, Enum):
    un = "un"
    pacote = "pacote"
    caixa = "caixa"
    ml = "ml"
    g = "g"
    par = "par"
    rolo = "rolo"
    kit = "kit"


class StockMovementType(str, Enum):
    purchase = "purchase"
    usage = "usage"
    adjustment = "adjustment"


class ExpenseRecurrence(str, Enum):
    one_time = "one_time"
    monthly = "monthly"
    weekly = "weekly"
    yearly = "yearly"


class AnamnesisHairLoss(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AnamnosisProcedureType(str, Enum):
    extension = "extension"
    permanent = "permanent"
    lash_lifting = "lash_lifting"


class CancelledBy(str, Enum):
    professional = "professional"
    client = "client"
