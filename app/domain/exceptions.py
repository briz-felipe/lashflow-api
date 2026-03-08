class DomainError(Exception):
    """Base class for domain-level exceptions."""


class InvalidStatusTransition(DomainError):
    """Raised when an appointment status transition is not allowed."""


class SlotUnavailable(DomainError):
    """Raised when the requested time slot is not available."""


class InsufficientStock(DomainError):
    """Raised when a usage movement would result in negative stock."""


class DuplicatePhone(DomainError):
    """Raised when a client with the same phone already exists."""


class AllergyDetailRequired(DomainError):
    """Raised when hasAllergy is True but allergyDetails is not provided."""
