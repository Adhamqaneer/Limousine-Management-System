"""One-time credential setup for a provisioned desktop database."""

from secrets import compare_digest, token_urlsafe
from threading import Lock

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import RedirectResponse

from limousine.infrastructure.migrations import migrate, needs_operator_setup

from ..rendering import render_page
from ..security import require_csrf

SETUP_COOKIE = "hspace_desktop_setup"
SETUP_PATH = "/desktop/setup/"


def register_routes(
    app,
    setup_token,
):
    database = app.state.database
    launch_lock = Lock()
    launch_used = False
    setup_session = token_urlsafe(32)

    def require_pending_setup():
        if not needs_operator_setup(database):
            raise HTTPException(404)

    def require_setup_session(request):
        supplied = request.cookies.get(
            SETUP_COOKIE,
            "",
        )
        if not compare_digest(
            supplied.encode(),
            setup_session.encode(),
        ):
            raise HTTPException(404)
        require_pending_setup()

    def setup_page(
        request,
        invalid=False,
    ):
        return render_page(
            request,
            "login.html",
            {"first_setup": True, "setup_invalid": invalid},
            status_code=400 if invalid else 200,
        )

    @app.get(SETUP_PATH)
    def desktop_first_run(
        request: Request,
        token: str = "",
    ):
        nonlocal launch_used
        if not token:
            require_setup_session(request)
            return setup_page(request)

        if not compare_digest(
            token.encode(),
            setup_token.encode(),
        ):
            raise HTTPException(404)
        with launch_lock:
            if launch_used:
                raise HTTPException(404)
            require_pending_setup()
            launch_used = True

        response = RedirectResponse(
            SETUP_PATH,
            303,
        )
        response.headers["Cache-Control"] = "no-store"
        response.set_cookie(
            SETUP_COOKIE,
            setup_session,
            path=SETUP_PATH,
            httponly=True,
            samesite="strict",
        )
        return response

    @app.post(SETUP_PATH)
    async def desktop_set_password(request: Request):
        async with request.form(
            max_files=0,
            max_fields=3,
            max_part_size=8192,
        ) as form:
            require_csrf(
                request,
                form.get("csrfmiddlewaretoken"),
            )
            await run_in_threadpool(
                require_setup_session,
                request,
            )
            password = form.get("password")
            if (
                not isinstance(
                    password,
                    str,
                )
                or password != form.get("confirmation")
                or not 8 <= len(password) <= 1024
                or password.isdigit()
            ):
                return setup_page(
                    request,
                    invalid=True,
                )
        await run_in_threadpool(
            migrate,
            database,
            operator_password=password,
        )
        response = RedirectResponse(
            "/login/",
            303,
        )
        response.delete_cookie(
            SETUP_COOKIE,
            path=SETUP_PATH,
        )
        return response
