"""Agreed vehicle fields, independent of frameworks and persistence."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime


class DomainError(ValueError):
    """Input does not satisfy the currently agreed vehicle rules."""


class NotFound(LookupError):
    """The requested vehicle or its attachment does not exist."""


def normalize_plate_number(value: str) -> str:
    """Preserve ASCII digits and optional hyphens between digit groups."""
    if not isinstance(value, str):
        raise DomainError("Enter a plate number.")
    value = value.strip()
    if not value:
        raise DomainError("Enter a plate number.")
    if len(value) > 64:
        raise DomainError("The plate number must be 64 characters or fewer.")
    if not re.fullmatch(r"[0-9]+(?:-[0-9]+)*", value):
        raise DomainError(
            "Use English digits, with optional hyphens between digits, for the vehicle number."
        )
    return value


VEHICLE_TEXT_FIELDS = {
    "owner_name": 200,
    "owner_phone": 32,
    "driver_name": 200,
    "driver_phone": 32,
    "vehicle_type": 120,
    "manufacture_year": 32,
    "chassis_number": 120,
}


def is_vehicle_name(value):
    """Allow English/Arabic letters, Arabic marks and spaces; require a letter."""
    has_letter = False
    for char in value:
        category = unicodedata.category(char)
        is_arabic_character = any(
            start <= ord(char) <= end
            for start, end in ((0x600, 0x6FF), (0x750, 0x77F), (0x8A0, 0x8FF))
        )
        is_english_letter = char.isascii() and char.isalpha()
        is_arabic_letter = is_arabic_character and category.startswith("L")
        is_arabic_mark = is_arabic_character and category.startswith("M")
        if is_english_letter or is_arabic_letter:
            has_letter = True
        elif char != " " and not (is_arabic_mark and has_letter):
            return False
    return has_letter


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
        if value:
            if (
                name in ("owner_name", "driver_name", "vehicle_type")
                and not is_vehicle_name(value)
            ):
                raise DomainError(
                    "Names and vehicle type accept Arabic or English letters and spaces only."
                )
            if name == "owner_phone" and not re.fullmatch(
                r"[0-9\u0660-\u0669\u06f0-\u06f9]+", value
            ):
                raise DomainError("The owner phone accepts digits only.")
            if (
                name in ("driver_phone", "manufacture_year")
                and not re.fullmatch(r"[0-9]+", value)
            ):
                raise DomainError("Driver phone and vehicle model accept English digits only.")
            if (
                name == "chassis_number"
                and not re.fullmatch(r"[A-Za-z0-9]+", value)
            ):
                raise DomainError("The chassis number accepts English letters and digits only.")
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
    driver_assignment_id: int | None = None
    category_id: int | None = None


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
    owner_name: str = ""
    owner_phone: str = ""
    driver_phone: str = ""
