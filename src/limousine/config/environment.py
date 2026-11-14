"""Small, strict environment readers shared by settings modules."""

import os

from django.core.exceptions import ImproperlyConfigured


def env_list(name, default=""):
    return [value.strip() for value in os.environ.get(name, default).split(",") if value.strip()]


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    value = value.strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    raise ImproperlyConfigured(f"{name} must be true or false.")
