"""Account identity, role and access rules independent of the web framework."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import unicodedata
from uuid import UUID

MAX_OPERATORS = 4

class Role(StrEnum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

@dataclass(frozen=True)
class User:
    id: UUID
    slot: int
    username: str
    role: Role
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    last_login: datetime | None = None

    @property
    def can_login(self):
        return self.is_active and not self.is_deleted

class AccessDenied(PermissionError):
    pass

def validate_slot(slot):
    if isinstance(slot, bool) or not isinstance(slot, int) or not 1 <= slot <= MAX_OPERATORS:
        raise ValueError("Choose an account slot from 1 to 4.")
    return slot

def normalize_username(value):
    if not isinstance(value, str):
        raise ValueError("Enter a username.")
    value = unicodedata.normalize("NFKC", value.strip())
    if not value or len(value) > 150 or any(not (char.isalnum() or char in " .@+-_") for char in value):
        raise ValueError("Use a name of up to 150 letters, numbers, spaces or . @ + - _.")
    return value

def authorize_account_change(actor, target, changes):
    if actor.role != Role.ADMIN or not actor.can_login:
        raise AccessDenied("Only the administrator can manage accounts.")
    if target.role == Role.ADMIN:
        raise AccessDenied("The administrator account cannot be disabled or deleted.")
    if not changes or set(changes) - {"is_active", "is_deleted"} or any(type(value) is not bool for value in changes.values()):
        raise ValueError("Provide boolean is_active or is_deleted values.")
    deleted = changes.get("is_deleted", target.is_deleted)
    active = changes.get("is_active", target.is_active)
    if deleted:
        active = False
    return active, deleted
