"""Choose document types and download the matching originals in one ZIP."""

from fastapi import Depends, Request
from starlette.concurrency import run_in_threadpool

from limousine.infrastructure.attachment_archive import build_vehicle_archive

from ..downloads import ArchiveResponse
from ..rendering import render_page
from ..security import current_user
from .categories import category_form


def register_routes(app):
    @app.get("/attachments/download/")
    def download_page(
        request: Request,
        user=Depends(current_user),
    ):
        return render_page(
            request,
            "attachment_download.html",
            user=user,
        )

    @app.post("/api/attachment-download/availability/")
    async def attachment_availability(
        request: Request,
        user=Depends(current_user),
    ):
        payload = await category_form(
            request,
            ("vehicle_ids", "category_ids"),
            ("vehicle_ids", "category_ids"),
        )
        return await run_in_threadpool(
            app.state.attachment_download.availability,
            payload["vehicle_ids"],
            payload["category_ids"],
            user,
        )

    @app.post("/api/attachment-download/")
    async def download_attachments(
        request: Request,
        user=Depends(current_user),
    ):
        payload = await category_form(
            request,
            ("vehicle_ids", "category_ids"),
            ("vehicle_ids", "category_ids"),
        )
        selection = await run_in_threadpool(
            app.state.attachment_download.select,
            payload["vehicle_ids"],
            payload["category_ids"],
            user,
        )
        archive = await run_in_threadpool(
            build_vehicle_archive,
            selection,
            app.state.store,
        )
        response = ArchiveResponse(
            archive,
            "HSPACE-attachments.zip",
        )
        response.headers["X-HSpace-File-Count"] = str(len(selection.files))
        response.headers["X-HSpace-Missing-Count"] = str(len(selection.missing))
        return response
