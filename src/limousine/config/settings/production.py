"""Production fails closed when required deployment configuration is missing."""

from django.core.exceptions import ImproperlyConfigured

from limousine.config.environment import env_bool

from .base import *  # noqa: F403

if not SECRET_KEY or len(SECRET_KEY) < 50 or SECRET_KEY.startswith("development-"):  # noqa: F405
    raise ImproperlyConfigured("Production requires a unique DJANGO_SECRET_KEY of at least 50 characters.")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("Production requires explicit DJANGO_ALLOWED_HOSTS; wildcard hosts are not allowed.")
if not ORACLE_CONFIGURED:  # noqa: F405
    raise ImproperlyConfigured("Production requires ORACLE_DSN, ORACLE_USER, and ORACLE_PASSWORD.")

DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^health/live/$", r"^health/ready/$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
# Enable only after verifying that all applicable subdomains support HTTPS.
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS")
SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD")

# Only enable behind a trusted proxy that strips and sets this header itself.
if env_bool("DJANGO_TRUST_PROXY"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
