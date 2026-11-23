"""Authentication guard and supported recovery records."""

from limousine.domain.accounts import AccessDenied
from limousine.domain.vehicles import DomainError

KINDS = ("vehicle", "attachment", "cover", "office")


def require_actor(actor):
    if actor is None:
        raise AccessDenied("Sign in to continue.")


def validate_kind(kind):
    if kind not in KINDS:
        raise DomainError("Unknown deleted item type.")
