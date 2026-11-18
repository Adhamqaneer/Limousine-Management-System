"""Security headers and safe public error responses."""

import psycopg
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse, RedirectResponse

from limousine.domain.accounts import AccessDenied
from limousine.domain.attachments import AttachmentNameConflict, AttachmentNameError
from limousine.domain.drivers import DriverValidationError
from limousine.domain.vehicles import DomainError, NotFound
from limousine.infrastructure.attachments import (
    MAX_ATTACHMENT_BYTES,
    AttachmentTooLarge,
)

from .security import AuthenticationRequired


def error(code, message, status):
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def configure_http(app, settings):
    @app.middleware("http")
    async def security_headers(request, call_next):
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return error("validation_error", "Invalid content length.", 400)
        if length > MAX_ATTACHMENT_BYTES + 65536:
            return error("file_too_large", "The file must be 10 MB or smaller.", 413)
        if settings.production and request.url.scheme != "https":
            return RedirectResponse(str(request.url.replace(scheme="https")), status_code=307)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if not request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "private, no-store"
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        return response

    @app.exception_handler(AuthenticationRequired)
    async def authentication_error(request, exc):
        return (
            error("authentication_required", "Sign in to continue.", 401)
            if request.url.path.startswith("/api/")
            else RedirectResponse("/login/", 303)
        )

    @app.exception_handler(AccessDenied)
    async def denied(request, exc):
        return error("forbidden", str(exc), 403)

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        if isinstance(exc, AttachmentNameConflict):
            return error("attachment_name_conflict", str(exc), 409)
        if isinstance(exc, AttachmentNameError):
            return error("invalid_attachment_name", str(exc), 400)
        if isinstance(exc, DriverValidationError):
            return JSONResponse(
                {
                    "error": {
                        "code": "driver_validation",
                        "message": str(exc),
                        "field": exc.field,
                        "reason": exc.reason,
                    }
                },
                status_code=400,
            )
        return error(
            "file_too_large" if isinstance(exc, AttachmentTooLarge) else "validation_error",
            str(exc),
            413 if isinstance(exc, AttachmentTooLarge) else 400,
        )

    @app.exception_handler(NotFound)
    async def missing(request, exc):
        return error("not_found", "This record could not be found.", 404)

    @app.exception_handler(psycopg.Error)
    async def database_error(request, exc):
        return error("storage_unavailable", "Storage is temporarily unavailable.", 503)

    @app.exception_handler(OSError)
    async def file_error(request, exc):
        return error(
            "not_found" if isinstance(exc, FileNotFoundError) else "storage_unavailable",
            "The file is unavailable.",
            404 if isinstance(exc, FileNotFoundError) else 503,
        )

    @app.exception_handler(RequestValidationError)
    async def request_error(request, exc):
        return error("validation_error", "Invalid request parameters.", 400)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error("request_failed", str(exc.detail), exc.status_code)
