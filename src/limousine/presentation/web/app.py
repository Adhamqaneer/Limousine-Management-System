"""Compose services and register HTTP features; start here to follow the web app."""

import mimetypes

from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.staticfiles import StaticFiles

from limousine.application.accounts import AccountService
from limousine.application.drivers import DriverService
from limousine.application.office import OfficeService
from limousine.application.recycling import RecyclingService
from limousine.application.vehicles import VehicleService
from limousine.config.runtime import ROOT, load_settings
from limousine.infrastructure.accounts import PostgresAccountRepository
from limousine.infrastructure.attachments import LocalAttachmentStore
from limousine.infrastructure.database import Database
from limousine.infrastructure.drivers import PostgresDriverRepository
from limousine.infrastructure.file_cleanup import FileCleanup
from limousine.infrastructure.media_layout import MediaOrganizer
from limousine.infrastructure.office import PostgresOfficeRepository
from limousine.infrastructure.vehicle_repository import PostgresVehicleRepository

from .http_errors import configure_http
from .routes import accounts, drivers, health, office, recycling, vehicles


def create_app(settings=None):
    # Windows MIME registries may omit WebP; serve local artwork consistently.
    mimetypes.add_type("image/webp", ".webp")
    settings = (settings or load_settings()).validate()
    app = FastAPI(title="H SPACE", version="2.0.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.state.database = Database(settings)
    app.state.store = LocalAttachmentStore(settings.media_root)
    app.state.cleanup = FileCleanup(app.state.database, app.state.store)
    app.state.media_layout = (
        MediaOrganizer(app.state.database, app.state.store)
        if settings.database_configured
        else None
    )
    app.state.accounts = PostgresAccountRepository(app.state.database)
    app.state.account_service = AccountService(app.state.accounts)
    app.state.vehicles = VehicleService(
        PostgresVehicleRepository(app.state.database, media_layout=app.state.media_layout)
    )
    app.state.recycling = RecyclingService(PostgresVehicleRepository(app.state.database))
    app.state.office = OfficeService(PostgresOfficeRepository(app.state.database))
    app.state.drivers = DriverService(
        PostgresDriverRepository(app.state.database, media_layout=app.state.media_layout)
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
    app.mount(
        "/static",
        StaticFiles(directory=str(ROOT / "src/limousine/presentation/web/static")),
        name="static",
    )

    configure_http(app, settings)
    health.register_routes(app)
    accounts.register_routes(app)
    vehicles.register_routes(app)
    drivers.register_routes(app)
    recycling.register_routes(app)
    office.register_routes(app)
    return app


app = create_app()
