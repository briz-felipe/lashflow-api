# Import all entities here to ensure SQLModel registers their table metadata
from app.domain.entities.user import User
from app.domain.entities.client import Client
from app.domain.entities.procedure import Procedure
from app.domain.entities.appointment import Appointment
from app.domain.entities.payment import Payment, PartialPaymentRecord
from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.material import Material
from app.domain.entities.stock_movement import StockMovement
from app.domain.entities.expense import Expense
from app.domain.entities.time_slot import TimeSlot
from app.domain.entities.blocked_date import BlockedDate

__all__ = [
    "User", "Client", "Procedure", "Appointment", "Payment",
    "PartialPaymentRecord", "Anamnesis", "Material", "StockMovement",
    "Expense", "TimeSlot", "BlockedDate",
]
