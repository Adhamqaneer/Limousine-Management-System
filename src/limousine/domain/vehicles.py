"""Agreed vehicle fields, independent of frameworks and persistence."""

from dataclasses import dataclass
from datetime import datetime
import unicodedata


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


VEHICLE_TEXT_FIELDS = {"vehicle_type": 120, "driver_name": 200, "chassis_number": 120, "manufacture_year": 32}


def normalize_vehicle_fields(fields):
    if set(fields) - set(VEHICLE_TEXT_FIELDS):
        raise DomainError("Unknown vehicle field.")
    result = {}
    for name, value in fields.items():
        if not isinstance(value, str):
            raise DomainError("Vehicle fields must be text.")
        value = value.strip()
        if name == "vehicle_type" and not value:
            raise DomainError("Enter a vehicle type.")
        if len(value) > VEHICLE_TEXT_FIELDS[name]:
            raise DomainError("A vehicle field exceeds its allowed length.")
        if any(unicodedata.category(char) == "Cc" for char in value):
            raise DomainError("Vehicle fields must be a single line of text.")
        result[name] = value
    return result


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
class VehicleCover:
    vehicle_id: int
    storage_key: str
    original_name: str
    size: int


@dataclass(frozen=True)
class Vehicle:
    id: int
    plate_number: str
    created_at: datetime
    attachments: tuple[Attachment, ...] = ()
    vehicle_type: str = ""
    driver_name: str = ""
    chassis_number: str = ""
    manufacture_year: str = ""
    cover: VehicleCover | None = None
