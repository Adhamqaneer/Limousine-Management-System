"""Vehicle data and validation, independent of Django and Oracle."""

from dataclasses import dataclass
from datetime import datetime


class DomainError(ValueError):
    """Input does not satisfy the currently agreed vehicle rules."""


class NotFound(LookupError):
    """The requested vehicle or its attachment does not exist."""


def normalize_plate_number(value: str) -> str:
    """Keep plate formats flexible until the company's fields are agreed."""
    if not isinstance(value, str):
        raise DomainError("Enter a plate number.")
    value = value.strip()
    if not value:
        raise DomainError("Enter a plate number.")
    if len(value) > 64:
        raise DomainError("The plate number must be 64 characters or fewer.")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise DomainError("The plate number must be a single line of text.")
    return value


@dataclass(frozen=True)
class Attachment:
    id: int
    vehicle_id: int
    storage_key: str
    original_name: str
    kind: str
    size: int
    created_at: datetime


@dataclass(frozen=True)
class Vehicle:
    id: int
    plate_number: str
    created_at: datetime
    attachments: tuple[Attachment, ...] = ()
