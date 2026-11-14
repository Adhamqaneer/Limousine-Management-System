"""Isolated HTTP/configuration tests. Never connects to a real database."""

import os

# This process is explicitly a no-database unit/HTTP test process.
# Empty values also stop .env loading from picking up developer credentials.
for variable in ("ORACLE_DSN", "ORACLE_USER", "ORACLE_PASSWORD"):
    os.environ[variable] = ""

from .base import *  # noqa: F403, E402

DEBUG = False
SECRET_KEY = "test-only-limousine-secret-key-123456789012345678901234567890"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
ORACLE_CONFIGURED = False
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa: F405
WHITENOISE_USE_FINDERS = True
