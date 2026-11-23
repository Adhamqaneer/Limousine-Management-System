"""Shared private upload, rename, preview and download HTTP handling."""

import logging
import re
from contextlib import nullcontext
from pathlib import PurePosixPath

import psycopg
from starlette.concurrency import run_in_threadpool
from starlette.responses import FileResponse, JSONResponse

from limousine.domain.categories import require_free_category
from limousine.domain.office import OfficeAttachment
from limousine.domain.vehicles import DomainError
from limousine.infrastructure.attachments import AttachmentTooLarge
from limousine.infrastructure.document_preview import PreviewUnavailable, office_preview

from .http_errors import error
from .rendering import render_page
from .requests import read_json_body
from .security import require_csrf
from .serializers import attachment_payload, vehicle_payload

logger = logging.getLogger(__name__)


class UploadAdapter:
    def __init__(self, upload):
        self.name, self.size, self.file = upload.filename, upload.size, upload.file

    def read(self, size):
        return self.file.read(size)


def store_upload(app, vehicle_id, upload, cover, actor, assignment_id=None, category_id=None):
    layout = app.state.media_layout
    with layout.operation() if layout else nullcontext():
        return _store_upload(app, vehicle_id, upload, cover, actor, assignment_id, category_id)


def _store_upload(app, vehicle_id, upload, cover, actor, assignment_id=None, category_id=None):
    category = app.state.categories.get(category_id) if category_id is not None else None
    if category:
        category_id = category["id"]
    service, store = app.state.vehicles, app.state.store
    vehicle = service.get_vehicle(vehicle_id)
    if (
        category
        and not cover
        and assignment_id is None
    ):
        require_free_category(
            category["is_other"],
            any(item.category_id == category_id for item in vehicle.attachments),
        )
    if assignment_id is not None:
        service.driver_attachments(vehicle_id, assignment_id)
    layout = app.state.media_layout
    directory = layout.upload_directory(vehicle_id, assignment_id) if layout else None
    folder_options = {"directory": directory} if directory else {}
    try:
        saved = (
            store.save_card_photo(UploadAdapter(upload), **folder_options)
            if cover
            else store.save(UploadAdapter(upload), **folder_options)
        )
    except AttachmentTooLarge:
        raise
    except DomainError as exc:
        return error("invalid_file", str(exc), 400)
    try:
        if cover:
            service.replace_cover(
                vehicle_id,
                storage_key=saved.storage_key,
                original_name=saved.original_name,
                size=saved.size,
                actor=actor,
            )
        else:
            item = service.add_attachment(
                vehicle_id,
                storage_key=saved.storage_key,
                original_name=saved.original_name,
                size=saved.size,
                kind=saved.kind,
                actor=actor,
                **({"category_id": category_id} if category_id is not None else {}),
                **({"assignment_id": assignment_id} if assignment_id is not None else {})
            )
    except Exception:
        try:
            app.state.cleanup.discard(saved.storage_key)
        except (OSError, psycopg.Error):
            logger.warning("Failed to clean an unsuccessful upload.")
        raise
    return JSONResponse(
        (
            {"vehicle": vehicle_payload(service.get_vehicle(vehicle_id), True)}
            if cover
            else {"attachment": attachment_payload(item)}
        ),
        status_code=201,
    )


async def upload_request(app, vehicle_id, request, cover, actor, assignment_id=None):
    require_csrf(request)
    async with request.form(max_files=1, max_fields=2) as form:
        upload, category_id = category_upload_form(form)
        return await run_in_threadpool(
            store_upload, app, vehicle_id, upload, cover, actor, assignment_id, category_id
        )


def upload_form_file(form, *, optional_fields=()):
    upload = form.get("file")
    if (
        set(form) - {"file", *optional_fields}
        or len(form.getlist("file")) != 1
        or not hasattr(upload, "file")
    ):
        raise DomainError("Choose one file.")
    return upload


def category_upload_form(form):
    upload = upload_form_file(form, optional_fields=("category_id",))
    if len(form.getlist("category_id")) > 1:
        raise DomainError("Choose one category.")
    value = form.get("category_id")
    if value is None:
        return upload, None
    if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]{0,18}", value):
        raise DomainError("Choose a valid category.")
    return upload, int(value)


def file_response(app, key, filename, preview):
    path = app.state.store.path(key)
    if not path.is_file():
        raise FileNotFoundError()
    response = FileResponse(
        path,
        filename=filename,
        media_type=app.state.store.content_type(key) if preview else "application/octet-stream",
        content_disposition_type="inline" if preview else "attachment",
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; base-uri 'none'; frame-ancestors 'self'"
    )
    return response


async def rename_attachment_request(
    app, vehicle_id, attachment_id, request, user, assignment_id=None, office=False
):
    require_csrf(request)
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise DomainError("Send the attachment name as JSON.")
    payload = await read_json_body(
        request,
        size_limit=4096,
        too_large_message="The attachment name is too large.",
        invalid_message="Invalid attachment name.",
    )
    if (
        not isinstance(payload, dict)
        or set(payload) != {"name", "expected_name"}
        or not isinstance(payload["expected_name"], str)
        or len(payload["expected_name"]) > 255
    ):
        raise DomainError("Provide the attachment name and its previous name.")
    if office:
        item = await run_in_threadpool(
            app.state.office.rename, attachment_id, payload["name"], payload["expected_name"], user
        )
    else:
        item = await run_in_threadpool(
            app.state.vehicles.rename_attachment,
            vehicle_id,
            attachment_id,
            payload["name"],
            payload["expected_name"],
            actor=user,
            **({"assignment_id": assignment_id} if assignment_id is not None else {})
        )
    return {"attachment": attachment_payload(item)}


def preview_item(app, item, request, user):
    extension = PurePosixPath(item.storage_key).suffix.lower()
    if extension not in (".docx", ".xlsx"):
        return file_response(app, item.storage_key, item.original_name, True)
    context = {
        "attachment": attachment_payload(item),
        "office_context": isinstance(item, OfficeAttachment),
    }
    try:
        with app.state.store.open(item.storage_key) as source:
            context["preview"] = office_preview(source, extension)
    except PreviewUnavailable:
        context["unavailable"] = True
    return render_page(request, "document_preview.html", context, user=user)


def store_office_upload(app, upload, actor):
    layout = app.state.media_layout
    with layout.operation() if layout else nullcontext():
        return _store_office_upload(app, upload, actor)


def _store_office_upload(app, upload, actor):
    saved = app.state.store.save_office_file(UploadAdapter(upload))
    try:
        item = app.state.office.add(
            saved.storage_key,
            saved.original_name,
            saved.kind,
            saved.size,
            actor,
        )
    except Exception:
        try:
            app.state.cleanup.discard(saved.storage_key)
        except (OSError, psycopg.Error):
            logger.warning("Failed to clean an unsuccessful office upload.")
        raise
    return JSONResponse({"attachment": attachment_payload(item)}, status_code=201)
