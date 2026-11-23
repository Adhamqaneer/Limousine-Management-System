"""Vehicles pages and API endpoints."""

from typing import Literal

from fastapi import Depends, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from limousine.infrastructure.attachment_archive import build_attachment_archive

from ..downloads import ArchiveResponse
from ..file_handlers import (
    file_response,
    preview_item,
    rename_attachment_request,
    upload_request,
)
from ..rendering import render_page
from ..requests import vehicle_fields
from ..security import current_user, require_csrf
from ..serializers import vehicle_payload


def register_routes(app):
    @app.get(
        "/",
        name="home",
    )
    def home(
        request: Request,
        user=Depends(current_user),
    ):
        return render_page(
            request,
            "home.html",
            user=user,
        )

    @app.get(
        "/reports/vehicles/",
        name="vehicle_report",
    )
    def vehicle_report(
        request: Request,
        user=Depends(current_user),
    ):
        return render_page(
            request,
            "vehicle_report.html",
            user=user,
        )

    @app.get("/api/vehicles/")
    def vehicles(user=Depends(current_user)):
        return {"vehicles": [vehicle_payload(item) for item in app.state.vehicles.list_vehicles()]}

    @app.post(
        "/api/vehicles/",
        status_code=201,
    )
    async def add_vehicle(
        request: Request,
        user=Depends(current_user),
    ):
        require_csrf(request)
        fields = await vehicle_fields(
            request,
            True,
        )
        vehicle = await run_in_threadpool(
            app.state.vehicles.create_vehicle,
            actor=user,
            **fields,
        )
        return {
            "vehicle": vehicle_payload(
                vehicle,
                True,
            )
        }

    @app.get("/api/vehicles/{vehicle_id}/")
    def detail(
        vehicle_id: int,
        user=Depends(current_user),
    ):
        return {
            "vehicle": vehicle_payload(
                app.state.vehicles.get_vehicle(vehicle_id),
                True,
            )
        }

    @app.patch("/api/vehicles/{vehicle_id}/")
    async def update_vehicle(
        vehicle_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        require_csrf(request)
        fields = await vehicle_fields(request)
        vehicle = await run_in_threadpool(
            app.state.vehicles.update_vehicle,
            vehicle_id,
            **fields,
        )
        return {
            "vehicle": vehicle_payload(
                vehicle,
                True,
            )
        }

    @app.post("/api/vehicles/{vehicle_id}/attachments/")
    async def upload_attachment(
        vehicle_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        return await upload_request(
            app,
            vehicle_id,
            request,
            False,
            user,
        )

    @app.post("/api/vehicles/{vehicle_id}/cover/")
    async def upload_cover(
        vehicle_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        return await upload_request(
            app,
            vehicle_id,
            request,
            True,
            user,
        )

    @app.delete(
        "/api/vehicles/{vehicle_id}/attachments/{attachment_id}/",
        status_code=204,
    )
    def delete_attachment(
        vehicle_id: int,
        attachment_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        require_csrf(request)
        app.state.vehicles.delete_attachment(
            vehicle_id,
            attachment_id,
            actor=user,
        )
        return Response(status_code=204)

    @app.delete(
        "/api/vehicles/{vehicle_id}/cover/",
        status_code=204,
    )
    def delete_cover(
        vehicle_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        require_csrf(request)
        app.state.vehicles.delete_cover(
            vehicle_id,
            actor=user,
        )
        return Response(status_code=204)

    @app.api_route(
        "/api/vehicles/{vehicle_id}/cover/",
        methods=["GET", "HEAD"],
    )
    def cover(
        vehicle_id: int,
        user=Depends(current_user),
    ):
        item = app.state.vehicles.get_cover(vehicle_id)
        return file_response(
            app,
            item.storage_key,
            item.original_name,
            True,
        )

    @app.api_route(
        "/api/vehicles/{vehicle_id}/attachments/{attachment_id}/download/",
        methods=["GET", "HEAD"],
    )
    def download(
        vehicle_id: int,
        attachment_id: int,
        user=Depends(current_user),
    ):
        item = app.state.vehicles.get_attachment(
            vehicle_id,
            attachment_id,
        )
        return file_response(
            app,
            item.storage_key,
            item.original_name,
            False,
        )

    @app.get("/api/vehicles/{vehicle_id}/attachments/archive/{kind}/")
    def download_archive(
        vehicle_id: int,
        kind: Literal["photos", "files"],
        user=Depends(current_user),
    ):
        batch = app.state.vehicles.prepare_attachment_download(
            vehicle_id,
            "image" if kind == "photos" else "file",
        )
        archive = build_attachment_archive(
            batch.attachments,
            app.state.store,
        )
        return ArchiveResponse(
            archive,
            f"HSPACE-{batch.plate_number}-{kind}.zip",
        )

    @app.patch("/api/vehicles/{vehicle_id}/attachments/{attachment_id}/")
    async def rename_attachment(
        vehicle_id: int,
        attachment_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        return await rename_attachment_request(
            app,
            vehicle_id,
            attachment_id,
            request,
            user,
        )

    @app.api_route(
        "/api/vehicles/{vehicle_id}/attachments/{attachment_id}/preview/",
        methods=["GET", "HEAD"],
    )
    def preview(
        vehicle_id: int,
        attachment_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        item = app.state.vehicles.get_attachment(
            vehicle_id,
            attachment_id,
        )
        return preview_item(
            app,
            item,
            request,
            user,
        )
