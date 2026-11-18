"""Shared deletion access and administrator-only recovery."""

from limousine.domain.accounts import AccessDenied, Role
from limousine.domain.vehicles import DomainError

KINDS = ("vehicle", "attachment", "cover", "office")


def require_actor(actor, *, restoring=False):
    if actor is None or not actor.can_login:
        raise AccessDenied("Sign in to continue.")
    if restoring and actor.role != Role.ADMIN:
        raise AccessDenied("Only the administrator can restore deleted items.")


def validate_kind(kind):
    if kind not in KINDS:
        raise DomainError("Unknown deleted item type.")
