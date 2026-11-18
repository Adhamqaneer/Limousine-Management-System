"""Accounts pages and API endpoints."""

from uuid import UUID

import psycopg
from fastapi import Depends, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import RedirectResponse

from limousine.domain.vehicles import DomainError

from ..rendering import render_page
from ..security import (
    SESSION_COOKIE,
    administrator,
    csrf_token,
    require_csrf,
    set_csrf_cookie,
)
from ..serializers import user_payload


def register_routes(app):
    settings = app.state.settings

    @app.get("/login/", name="login")
    def login_page(request: Request):
        unavailable = not settings.database_configured
        try:
            if request.cookies.get(SESSION_COOKIE) and app.state.accounts.session_user(
                request.cookies[SESSION_COOKIE]
            ):
                return RedirectResponse("/", 303)
        except psycopg.Error:
            unavailable = True
        return render_page(
            request, "login.html", {"unavailable": unavailable, "invalid": False, "username": ""}
        )

    @app.post("/login/")
    async def login_submit(request: Request):
        async with request.form(max_files=0, max_fields=3) as form:
            require_csrf(request, form.get("csrfmiddlewaretoken"))
            username, password = form.get("username", ""), form.get("password", "")
            if (
                not isinstance(username, str)
                or len(username) > 150
                or not isinstance(password, str)
                or len(password) > 1024
            ):
                raise DomainError("Invalid sign-in form.")
            unavailable = not settings.database_configured
            user = None
            try:
                if not unavailable:
                    user = await run_in_threadpool(
                        app.state.account_service.authenticate, username, password
                    )
                if user:
                    await run_in_threadpool(
                        app.state.accounts.delete_session, request.cookies.get(SESSION_COOKIE, "")
                    )
                    session = await run_in_threadpool(
                        app.state.accounts.create_session, user.id, settings.session_seconds
                    )
                    response = RedirectResponse("/", 303)
                    response.set_cookie(
                        SESSION_COOKIE,
                        session,
                        httponly=True,
                        secure=settings.production,
                        samesite="lax",
                        max_age=settings.session_seconds,
                    )
                    set_csrf_cookie(response, csrf_token(settings, session), settings)
                    return response
            except psycopg.Error:
                unavailable = True
            return render_page(
                request,
                "login.html",
                {"unavailable": unavailable, "invalid": not unavailable, "username": username},
                status_code=503 if unavailable else 200,
            )

    @app.post("/logout/", name="logout")
    async def logout(request: Request):
        async with request.form(max_files=0, max_fields=2) as form:
            require_csrf(request, form.get("csrfmiddlewaretoken"))
            await run_in_threadpool(
                app.state.accounts.delete_session, request.cookies.get(SESSION_COOKIE, "")
            )
        response = RedirectResponse("/login/", 303)
        response.delete_cookie(SESSION_COOKIE)
        set_csrf_cookie(response, csrf_token(settings), settings)
        return response

    @app.get("/users/", name="users")
    def users_page(request: Request, user=Depends(administrator)):
        return render_page(request, "users.html", user=user)

    @app.get("/api/users/")
    def users(user=Depends(administrator)):
        return {"users": [user_payload(item) for item in app.state.accounts.list_users()]}

    @app.patch("/api/users/{user_id}/")
    async def change_user(user_id: UUID, request: Request, user=Depends(administrator)):
        require_csrf(request)
        body = await request.body()
        if len(body) > 2048:
            raise DomainError("Account form is too large.")
        try:
            import json

            changes = json.loads(body)
            if not isinstance(changes, dict):
                raise ValueError()
            updated = await run_in_threadpool(
                app.state.account_service.change_status, user, user_id, changes
            )
        except (ValueError, TypeError):
            raise DomainError("Provide boolean account status fields.") from None
        return {"user": user_payload(updated)}
