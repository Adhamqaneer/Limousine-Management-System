"""Health pages and API endpoints."""

from starlette.responses import JSONResponse


def register_routes(app):
    @app.get("/health/live/")
    def live():
        return {"status": "ok"}

    @app.get("/health/ready/")
    def ready():
        status = app.state.database.ready()
        return JSONResponse(
            {"status": "ok" if status == "ok" else "not_ready", "database": status},
            status_code=200 if status == "ok" else 503,
        )
