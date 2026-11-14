"""Local development: application pages work before Oracle is provisioned."""

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = SECRET_KEY or "development-only-limousine-key-do-not-use-in-production-123456789"  # noqa: F405
ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1", "[::1]"]  # noqa: F405
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa: F405
WHITENOISE_USE_FINDERS = True
