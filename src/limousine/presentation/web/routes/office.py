"""Office pages and API endpoints."""

from typing import Literal

from fastapi import Depends, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from limousine.infrastructure.attachment_archive import build_attachment_archive

from ..downloads import ArchiveResponse
from ..file_handlers import (
    category_upload_form,
    file_response,
    preview_item,
    rename_attachment_request,
    store_office_upload,
)
from ..rendering import render_page
from ..security import current_user, require_csrf
from ..serializers import attachment_payload


def register_routes(app):
    @app.get("/office/")
    def office_page(request: Request, user=Depends(current_user)):
        return render_page(request, "office.html", user=user)

    @app.get("/api/office/attachments/")
    def office_files(user=Depends(current_user)):
        return {"attachments": [attachment_payload(item) for item in app.state.office.list_files()]}

    @app.post("/api/office/attachments/")
    async def upload_office_file(request: Request, user=Depends(current_user)):
        require_csrf(request)
        async with request.form(max_files=1, max_fields=2) as form:
            upload, category_id = category_upload_form(form)
            return await run_in_threadpool(store_office_upload, app, upload, user, category_id)

    @app.get("/api/office/attachments/archive/{kind}/")
    def office_archive(kind: Literal["photos", "files"], user=Depends(current_user)):
        items = app.state.office.download("image" if kind == "photos" else "file")
        return ArchiveResponse(
            build_attachment_archive(items, app.state.store), f"HSPACE-office-{kind}.zip"
        )

    @app.patch("/api/office/attachments/{attachment_id}/")
    async def rename_office_file(attachment_id: int, request: Request, user=Depends(current_user)):
        return await rename_attachment_request(app, None, attachment_id, request, user, office=True)

    @app.delete("/api/office/attachments/{attachment_id}/", status_code=204)
    def delete_office_file(attachment_id: int, request: Request, user=Depends(current_user)):
        require_csrf(request)
        app.state.office.delete(attachment_id, user)
        return Response(status_code=204)

    @app.api_route("/api/office/attachments/{attachment_id}/download/", methods=["GET", "HEAD"])
    def download_office_file(attachment_id: int, user=Depends(current_user)):
        item = app.state.office.get(attachment_id)
        return file_response(app, item.storage_key, item.original_name, False)

    @app.api_route("/api/office/attachments/{attachment_id}/preview/", methods=["GET", "HEAD"])
    def preview_office_file(attachment_id: int, request: Request, user=Depends(current_user)):
        return preview_item(app, app.state.office.get(attachment_id), request, user)
