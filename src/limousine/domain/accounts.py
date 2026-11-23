"""Identity for the office sign-in and actor-attributed records."""

from dataclasses import dataclass
from uuid import UUID

OPERATOR_USERNAME = "H space"


@dataclass(frozen=True)
class User:
    id: UUID
    username: str


class AccessDenied(PermissionError):
    pass
