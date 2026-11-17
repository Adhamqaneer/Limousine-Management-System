"""FastAPI HTTP adaptation; business rules and persistence stay outside routes."""
import logging
from pathlib import PurePosixPath
from uuid import UUID
import psycopg
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse, RedirectResponse, FileResponse, Response
from starlette.staticfiles import StaticFiles
from limousine.config.runtime import load_settings, ROOT
from limousine.application.vehicles import VehicleService
from limousine.application.recycling import RecyclingService
from limousine.application.drivers import DriverService
from limousine.infrastructure.drivers import PostgresDriverRepository
from limousine.application.accounts import AccountService
from limousine.domain.vehicles import DomainError, NotFound
from limousine.domain.accounts import AccessDenied
from limousine.infrastructure.database import Database
from limousine.infrastructure.file_cleanup import FileCleanup
from limousine.infrastructure.accounts import PostgresAccountRepository
from limousine.infrastructure.vehicle_repository import PostgresVehicleRepository
from limousine.infrastructure.attachments import LocalAttachmentStore, AttachmentTooLarge, MAX_ATTACHMENT_BYTES
from limousine.infrastructure.document_preview import office_preview, PreviewUnavailable
from .security import current_user, administrator, AuthenticationRequired, require_csrf, csrf_token, set_csrf_cookie, SESSION_COOKIE
from .rendering import render_page

logger = logging.getLogger(__name__)

def error(code, message, status):
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)

def attachment_payload(item):
    base = f"/api/vehicles/{item.vehicle_id}/attachments/{item.id}"
    return {"id": item.id, "name": item.original_name, "kind": item.kind, "size": item.size,
            "uploaded_at": item.created_at.isoformat(), "download_url": base + "/download/", "preview_url": base + "/preview/"}

def vehicle_payload(item, detailed=False):
    payload = {"id": item.id, "plate_number": item.plate_number, "vehicle_type": item.vehicle_type,
        "driver_name": item.driver_name, "chassis_number": item.chassis_number, "manufacture_year": item.manufacture_year,
        "owner_name": item.owner_name, "owner_phone": item.owner_phone, "driver_phone": item.driver_phone,
        "created_at": item.created_at.isoformat(), "attachment_count": len(item.attachments),
        "cover_url": f"/api/vehicles/{item.id}/cover/" if item.cover else None}
    if detailed:
        payload["attachments"] = [attachment_payload(file) for file in item.attachments]
    return payload

def user_payload(user):
    return {"id": str(user.id), "slot": user.slot, "username": user.username, "role": user.role.value,
        "is_active": user.is_active, "is_deleted": user.is_deleted,
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None}

async def vehicle_fields(request, creating=False):
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise DomainError("Send vehicle details as JSON.")
    body = await request.body()
    if len(body) > 8192:
        raise DomainError("The vehicle form is too large.")
    import json
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise DomainError("Invalid JSON.") from None
    allowed = {"plate_number", "vehicle_type", "driver_name", "chassis_number", "manufacture_year", "owner_name", "owner_phone", "driver_phone"}
    if not isinstance(payload, dict) or not payload or set(payload) - allowed:
        raise DomainError("Provide only the agreed vehicle fields.")
    if creating and not {"plate_number", "vehicle_type"}.issubset(payload):
        raise DomainError("Provide vehicle type and plate number.")
    return payload

class UploadAdapter:
    def __init__(self, upload):
        self.name, self.size, self.file = upload.filename, upload.size, upload.file
    def read(self, size):
        return self.file.read(size)

def create_app(settings=None):
    settings = (settings or load_settings()).validate()
    app = FastAPI(title="H SPACE", version="2.0.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.state.database = Database(settings)
    app.state.accounts = PostgresAccountRepository(app.state.database)
    app.state.account_service = AccountService(app.state.accounts)
    app.state.vehicles = VehicleService(PostgresVehicleRepository(app.state.database))
    app.state.recycling = RecyclingService(PostgresVehicleRepository(app.state.database))
    app.state.drivers = DriverService(PostgresDriverRepository(app.state.database))
    app.state.store = LocalAttachmentStore(settings.media_root)
    app.state.cleanup = FileCleanup(app.state.database, app.state.store)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
    app.mount("/static", StaticFiles(directory=str(ROOT / "src/limousine/presentation/web/static")), name="static")

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
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        return response

    @app.exception_handler(AuthenticationRequired)
    async def authentication_error(request, exc):
        return error("authentication_required", "Sign in to continue.", 401) if request.url.path.startswith("/api/") else RedirectResponse("/login/", 303)

    @app.exception_handler(AccessDenied)
    async def denied(request, exc):
        return error("forbidden", str(exc), 403)

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return error("file_too_large" if isinstance(exc, AttachmentTooLarge) else "validation_error", str(exc),
                     413 if isinstance(exc, AttachmentTooLarge) else 400)

    @app.exception_handler(NotFound)
    async def missing(request, exc):
        return error("not_found", "This record could not be found.", 404)

    @app.exception_handler(psycopg.Error)
    async def database_error(request, exc):
        return error("storage_unavailable", "Storage is temporarily unavailable.", 503)

    @app.exception_handler(OSError)
    async def file_error(request, exc):
        return error("not_found" if isinstance(exc, FileNotFoundError) else "storage_unavailable",
                     "The file is unavailable.", 404 if isinstance(exc, FileNotFoundError) else 503)

    @app.exception_handler(RequestValidationError)
    async def request_error(request, exc):
        return error("validation_error", "Invalid request parameters.", 400)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error("request_failed", str(exc.detail), exc.status_code)

    @app.get("/health/live/")
    def live():
        return {"status": "ok"}

    @app.get("/health/ready/")
    def ready():
        status = app.state.database.ready()
        return JSONResponse({"status": "ok" if status == "ok" else "not_ready", "database": status},
                            status_code=200 if status == "ok" else 503)

    @app.get("/", name="home")
    def home(request: Request, user=Depends(current_user)):
        return render_page(request, "home.html", user=user)

    @app.get("/login/", name="login")
    def login_page(request: Request):
        unavailable = not settings.database_configured
        try:
            if request.cookies.get(SESSION_COOKIE) and app.state.accounts.session_user(request.cookies[SESSION_COOKIE]):
                return RedirectResponse("/", 303)
        except psycopg.Error:
            unavailable = True
        return render_page(request, "login.html", {"unavailable": unavailable, "invalid": False, "username": ""})

    @app.post("/login/")
    async def login_submit(request: Request):
        async with request.form(max_files=0, max_fields=3) as form:
            require_csrf(request, form.get("csrfmiddlewaretoken"))
            username, password = form.get("username", ""), form.get("password", "")
            if not isinstance(username, str) or len(username) > 150 or not isinstance(password, str) or len(password) > 1024:
                raise DomainError("Invalid sign-in form.")
            unavailable = not settings.database_configured
            user = None
            try:
                if not unavailable:
                    user = await run_in_threadpool(app.state.account_service.authenticate, username, password)
                if user:
                    await run_in_threadpool(app.state.accounts.delete_session, request.cookies.get(SESSION_COOKIE, ""))
                    session = await run_in_threadpool(app.state.accounts.create_session, user.id, settings.session_seconds)
                    response = RedirectResponse("/", 303)
                    response.set_cookie(SESSION_COOKIE, session, httponly=True, secure=settings.production,
                                        samesite="lax", max_age=settings.session_seconds)
                    set_csrf_cookie(response, csrf_token(settings, session), settings)
                    return response
            except psycopg.Error:
                unavailable = True
            return render_page(request, "login.html", {"unavailable": unavailable, "invalid": not unavailable,
                "username": username}, status_code=503 if unavailable else 200)

    @app.post("/logout/", name="logout")
    async def logout(request: Request):
        async with request.form(max_files=0, max_fields=2) as form:
            require_csrf(request, form.get("csrfmiddlewaretoken"))
            await run_in_threadpool(app.state.accounts.delete_session, request.cookies.get(SESSION_COOKIE, ""))
        response = RedirectResponse("/login/", 303)
        response.delete_cookie(SESSION_COOKIE)
        set_csrf_cookie(response, csrf_token(settings), settings)
        return response

    @app.get("/reports/vehicles/", name="vehicle_report")
    def vehicle_report(request: Request, user=Depends(current_user)):
        return render_page(request, "vehicle_report.html", user=user)

    @app.get("/api/vehicles/")
    def vehicles(user=Depends(current_user)):
        return {"vehicles": [vehicle_payload(item) for item in app.state.vehicles.list_vehicles()]}

    @app.post("/api/vehicles/", status_code=201)
    async def add_vehicle(request: Request, user=Depends(current_user)):
        require_csrf(request)
        fields = await vehicle_fields(request, True)
        vehicle = await run_in_threadpool(app.state.vehicles.create_vehicle, actor=user, **fields)
        return {"vehicle": vehicle_payload(vehicle, True)}

    @app.get("/api/vehicles/{vehicle_id}/")
    def detail(vehicle_id: int, user=Depends(current_user)):
        return {"vehicle": vehicle_payload(app.state.vehicles.get_vehicle(vehicle_id), True)}

    @app.patch("/api/vehicles/{vehicle_id}/")
    async def update_vehicle(vehicle_id: int, request: Request, user=Depends(current_user)):
        require_csrf(request)
        fields = await vehicle_fields(request)
        vehicle = await run_in_threadpool(app.state.vehicles.update_vehicle, vehicle_id, **fields)
        return {"vehicle": vehicle_payload(vehicle, True)}

    def store_upload(vehicle_id, upload, cover, actor):
        service, store = app.state.vehicles, app.state.store
        service.get_vehicle(vehicle_id)
        try:
            saved = store.save_card_photo(UploadAdapter(upload)) if cover else store.save(UploadAdapter(upload))
        except AttachmentTooLarge:
            raise
        except DomainError as exc:
            return error("invalid_file", str(exc), 400)
        try:
            if cover:
                service.replace_cover(vehicle_id, storage_key=saved.storage_key, original_name=saved.original_name, size=saved.size, actor=actor)
            else:
                item = service.add_attachment(vehicle_id, storage_key=saved.storage_key, original_name=saved.original_name, size=saved.size, kind=saved.kind, actor=actor)
        except Exception:
            try:
                app.state.cleanup.discard(saved.storage_key)
            except (OSError, psycopg.Error):
                logger.warning("Failed to clean an unsuccessful upload.")
            raise
        return JSONResponse({"vehicle": vehicle_payload(service.get_vehicle(vehicle_id), True)} if cover else {"attachment": attachment_payload(item)}, status_code=201)

    async def upload_request(vehicle_id, request, cover, actor):
        require_csrf(request)
        async with request.form(max_files=1, max_fields=1) as form:
            upload = form.get("file")
            if len(form) != 1 or len(form.getlist("file")) != 1 or not hasattr(upload, "file"):
                raise DomainError("Choose exactly one file.")
            return await run_in_threadpool(store_upload, vehicle_id, upload, cover, actor)

    @app.post("/api/vehicles/{vehicle_id}/attachments/")
    async def upload_attachment(vehicle_id: int, request: Request, user=Depends(current_user)):
        return await upload_request(vehicle_id, request, False, user)

    @app.post("/api/vehicles/{vehicle_id}/cover/")
    async def upload_cover(vehicle_id: int, request: Request, user=Depends(current_user)):
        return await upload_request(vehicle_id, request, True, user)

    @app.delete("/api/vehicles/{vehicle_id}/attachments/{attachment_id}/", status_code=204)
    def delete_attachment(vehicle_id: int, attachment_id: int, request: Request, user=Depends(current_user)):
        require_csrf(request)
        app.state.vehicles.delete_attachment(vehicle_id, attachment_id, actor=user)
        return Response(status_code=204)

    @app.delete("/api/vehicles/{vehicle_id}/cover/", status_code=204)
    def delete_cover(vehicle_id: int, request: Request, user=Depends(current_user)):
        require_csrf(request)
        app.state.vehicles.delete_cover(vehicle_id, actor=user)
        return Response(status_code=204)

    @app.delete('/api/vehicles/{vehicle_id}/', status_code=204)
    def delete_vehicle(vehicle_id: int, request: Request, user=Depends(current_user)):
        require_csrf(request)
        app.state.recycling.delete_vehicle(vehicle_id, user)
        return Response(status_code=204)

    @app.get('/recycle-bin/')
    def recycle_bin(request: Request, user=Depends(administrator)):
        return render_page(request, 'recycle_bin.html', user=user)

    @app.get('/api/recycle-bin/')
    def deleted_items(user=Depends(administrator)):
        return {'items': app.state.recycling.list_deleted(user)}

    @app.post('/api/recycle-bin/{kind}/{item_id}/restore/', status_code=204)
    def restore_item(kind: str, item_id: int, request: Request, user=Depends(administrator)):
        require_csrf(request)
        app.state.recycling.restore_item(kind, item_id, user)
        return Response(status_code=204)

    @app.get('/api/activity/')
    def activity(before: int | None = None, user=Depends(administrator)):
        if before is not None and before < 1:
            raise DomainError('Invalid activity cursor.')
        return {'events': app.state.recycling.list_activity(user, before)}

    @app.get('/drivers/')
    def driver_history_page(request: Request,user=Depends(current_user)):
        return render_page(request,'drivers.html',user=user)

    @app.get('/api/drivers/')
    def driver_history(vehicle_id:int|None=None,q:str='',on_date:str|None=None,user=Depends(current_user)):
        return {'assignments':app.state.drivers.history(vehicle_id,q,on_date)}

    @app.get('/api/vehicles/{vehicle_id}/drivers/')
    def vehicle_drivers(vehicle_id:int,user=Depends(current_user)):
        return {'assignments':app.state.drivers.history(vehicle_id),'corrections':app.state.drivers.corrections(vehicle_id)}

    async def driver_request(vehicle_id,request,user,correcting):
        require_csrf(request)
        body=await request.body()
        if len(body)>4096:raise DomainError('Driver form is too large.')
        import json
        try:payload=json.loads(body)
        except (ValueError,UnicodeDecodeError):raise DomainError('Invalid driver form.') from None
        if not isinstance(payload,dict) or set(payload)!={'driver_name','driver_phone','started_on'}:raise DomainError('Provide driver name, phone and start date only.')
        method=app.state.drivers.correct if correcting else app.state.drivers.assign
        await run_in_threadpool(method,vehicle_id,payload['driver_name'],payload['driver_phone'],payload['started_on'],user)
        return {'vehicle':vehicle_payload(app.state.vehicles.get_vehicle(vehicle_id),True)}

    @app.post('/api/vehicles/{vehicle_id}/drivers/')
    async def assign_driver(vehicle_id:int,request:Request,user=Depends(current_user)):
        return await driver_request(vehicle_id,request,user,False)

    @app.patch('/api/vehicles/{vehicle_id}/drivers/current/')
    async def correct_driver(vehicle_id:int,request:Request,user=Depends(current_user)):
        return await driver_request(vehicle_id,request,user,True)

    def file_response(key, filename, preview):
        path = app.state.store.path(key)
        if not path.is_file():
            raise FileNotFoundError()
        response = FileResponse(path, filename=filename,
            media_type=app.state.store.content_type(key) if preview else "application/octet-stream",
            content_disposition_type="inline" if preview else "attachment")
        response.headers["Content-Security-Policy"] = "default-src 'none'; base-uri 'none'; frame-ancestors 'self'"
        return response

    @app.api_route("/api/vehicles/{vehicle_id}/cover/", methods=["GET", "HEAD"])
    def cover(vehicle_id: int, user=Depends(current_user)):
        item = app.state.vehicles.get_cover(vehicle_id)
        return file_response(item.storage_key, item.original_name, True)

    @app.api_route("/api/vehicles/{vehicle_id}/attachments/{attachment_id}/download/", methods=["GET", "HEAD"])
    def download(vehicle_id: int, attachment_id: int, user=Depends(current_user)):
        item = app.state.vehicles.get_attachment(vehicle_id, attachment_id)
        return file_response(item.storage_key, item.original_name, False)

    @app.api_route("/api/vehicles/{vehicle_id}/attachments/{attachment_id}/preview/", methods=["GET", "HEAD"])
    def preview(vehicle_id: int, attachment_id: int, request: Request, user=Depends(current_user)):
        item = app.state.vehicles.get_attachment(vehicle_id, attachment_id)
        extension = PurePosixPath(item.storage_key).suffix.lower()
        if extension not in (".docx", ".xlsx"):
            return file_response(item.storage_key, item.original_name, True)
        context = {"attachment": attachment_payload(item)}
        try:
            with app.state.store.open(item.storage_key) as source:
                context["preview"] = office_preview(source, extension)
        except PreviewUnavailable:
            context["unavailable"] = True
        return render_page(request, "document_preview.html", context, user=user)

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
            updated = await run_in_threadpool(app.state.account_service.change_status, user, user_id, changes)
        except (ValueError, TypeError):
            raise DomainError("Provide boolean account status fields.") from None
        return {"user": user_payload(updated)}

    return app

app = create_app()
