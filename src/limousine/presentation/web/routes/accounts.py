"""Office sign-in and sign-out."""

import psycopg
from fastapi import Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import RedirectResponse

from limousine.domain.vehicles import DomainError

from ..rendering import render_page
from ..security import (
    SESSION_COOKIE,
    csrf_token,
    require_csrf,
    set_csrf_cookie,
)


def register_routes(app):
    settings = app.state.settings

    @app.get(
        "/login/",
        name="login",
    )
    def login_page(request: Request):
        unavailable = not settings.database_configured
        try:
            if (
                request.cookies.get(SESSION_COOKIE)
                and app.state.accounts.session_user(
                request.cookies[SESSION_COOKIE]
            )
            ):
                return RedirectResponse(
                    "/",
                    303,
                )
        except psycopg.Error:
            unavailable = True
        return render_page(
            request,
            "login.html",
            {"unavailable": unavailable, "invalid": False, "username": ""},
        )

    @app.post("/login/")
    async def login_submit(request: Request):
        async with request.form(
            max_files=0,
            max_fields=3,
        ) as form:
            require_csrf(
                request,
                form.get("csrfmiddlewaretoken"),
            )
            username, password = form.get(
                "username",
                "",
            ), form.get(
                "password",
                "",
            )
            if (
                not isinstance(
                    username,
                    str,
                )
                or len(username) > 150
                or not isinstance(
                    password,
                    str,
                )
                or len(password) > 1024
            ):
                raise DomainError("Invalid sign-in form.")
            unavailable = not settings.database_configured
            session = None
            try:
                if not unavailable:
                    session = await run_in_threadpool(
                        app.state.account_service.sign_in,
                        username,
                        password,
                        settings.session_seconds,
                        request.cookies.get(
                            SESSION_COOKIE,
                            "",
                        ),
                    )
                if session:
                    response = RedirectResponse(
                        "/",
                        303,
                    )
                    response.set_cookie(
                        SESSION_COOKIE,
                        session,
                        httponly=True,
                        secure=settings.production,
                        samesite="lax",
                        max_age=settings.session_seconds,
                    )
                    set_csrf_cookie(
                        response,
                        csrf_token(
                            settings,
                            session,
                        ),
                        settings,
                    )
                    return response
            except psycopg.Error:
                unavailable = True
            return render_page(
                request,
                "login.html",
                {"unavailable": unavailable, "invalid": not unavailable, "username": username},
                status_code=503 if unavailable else 200,
            )

    @app.post(
        "/logout/",
        name="logout",
    )
    async def logout(request: Request):
        async with request.form(
            max_files=0,
            max_fields=2,
        ) as form:
            require_csrf(
                request,
                form.get("csrfmiddlewaretoken"),
            )
            await run_in_threadpool(
                app.state.accounts.delete_session,
                request.cookies.get(
                    SESSION_COOKIE,
                    "",
                ),
            )
        response = RedirectResponse(
            "/login/",
            303,
        )
        response.delete_cookie(SESSION_COOKIE)
        set_csrf_cookie(
            response,
            csrf_token(settings),
            settings,
        )
        return response
