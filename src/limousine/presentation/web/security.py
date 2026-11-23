"""Opaque session cookies and signed, session-bound double-submit CSRF."""

import hashlib
import hmac
import secrets

from fastapi import Request

SESSION_COOKIE = "hspace_session"


class AuthenticationRequired(Exception):
    pass


def current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE, "")
    user = request.app.state.accounts.session_user(token) if token else None
    if user is None:
        raise AuthenticationRequired()
    return user


def csrf_token(settings, session=""):
    nonce = secrets.token_urlsafe(24)
    signature = hmac.new(
        settings.secret.encode(), (session + ":" + nonce).encode(), hashlib.sha256
    ).hexdigest()
    return nonce + "." + signature


def valid_csrf(request, submitted):
    cookie = request.cookies.get("csrftoken", "")
    if (
        not isinstance(submitted, str)
        or not cookie
        or len(cookie) > 160
        or not secrets.compare_digest(cookie, submitted)
    ):
        return False
    try:
        nonce, signature = cookie.split(".")
    except ValueError:
        return False
    expected = hmac.new(
        request.app.state.settings.secret.encode(),
        (request.cookies.get(SESSION_COOKIE, "") + ":" + nonce).encode(),
        hashlib.sha256,
    ).hexdigest()
    return secrets.compare_digest(signature, expected)


def set_csrf_cookie(response, token, settings):
    response.set_cookie(
        "csrftoken",
        token,
        secure=settings.production,
        httponly=False,
        samesite="lax",
        max_age=settings.session_seconds,
    )


def require_csrf(request, submitted=None):
    if not valid_csrf(request, submitted or request.headers.get("x-csrftoken")):
        from fastapi import HTTPException

        raise HTTPException(403, "Reload the page and try again.")
