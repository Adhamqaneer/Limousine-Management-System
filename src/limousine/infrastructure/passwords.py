"""PBKDF2 password hashing with existing account compatibility."""

import base64
import hashlib
import hmac
import secrets
import warnings
from getpass import GetPassWarning, getpass

ITERATIONS = 1_000_000


def prompt_password():
    with warnings.catch_warnings():
        warnings.simplefilter("error", GetPassWarning)
        password = getpass("H space password: ")
        if password != getpass("Confirm H space password: "):
            raise ValueError("Passwords do not match.")
    return password


def hash_password(password):
    if (
        not isinstance(password, str)
        or not 8 <= len(password) <= 1024
        or password.isdigit()
    ):
        raise ValueError("Use a password of 8 to 1024 characters, not only numbers.")
    salt = secrets.token_urlsafe(12)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${base64.b64encode(digest).decode()}"


def verify_password(password, encoded):
    try:
        algorithm, count, salt, digest = encoded.split("$")
        iterations = int(count)
        if (
            algorithm != "pbkdf2_sha256"
            or not 1 <= iterations <= 10_000_000
            or len(password) > 1024
        ):
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
        return hmac.compare_digest(base64.b64encode(actual).decode(), digest)
    except (ValueError, TypeError, AttributeError):
        return False
