"""Drivers pages and API endpoints."""

from fastapi import Depends, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from limousine.domain.vehicles import DomainError

from ..file_handlers import (
    file_response,
    preview_item,
    rename_attachment_request,
    upload_request,
)
from ..rendering import render_page
from ..requests import read_json_body
from ..security import current_user, require_csrf
from ..serializers import attachment_payload, vehicle_payload


def register_routes(app):
    @app.get("/drivers/")
    def driver_history_page(request: Request, user=Depends(current_user)):
        return render_page(request, "drivers.html", user=user)

    @app.get("/api/drivers/")
    def driver_history(
        vehicle_id: int | None = None,
        q: str = "",
        on_date: str | None = None,
        user=Depends(current_user),
    ):
        return {"assignments": app.state.drivers.history(vehicle_id, q, on_date)}

    @app.get("/api/vehicles/{vehicle_id}/drivers/")
    def vehicle_drivers(vehicle_id: int, user=Depends(current_user)):
        return {
            "assignments": app.state.drivers.history(vehicle_id),
            "corrections": app.state.drivers.corrections(vehicle_id),
        }

    async def driver_request(vehicle_id, request, user, correcting):
        require_csrf(request)
        payload = await read_json_body(
            request,
            size_limit=4096,
            too_large_message="Driver form is too large.",
            invalid_message="Invalid driver form.",
        )
        if not isinstance(payload, dict) or set(payload) != {
            "driver_name",
            "driver_phone",
            "started_on",
        }:
            raise DomainError("Provide driver name, phone and start date only.")
        method = app.state.drivers.correct if correcting else app.state.drivers.assign
        await run_in_threadpool(
            method,
            vehicle_id,
            payload["driver_name"],
            payload["driver_phone"],
            payload["started_on"],
            user,
        )
        return {"vehicle": vehicle_payload(app.state.vehicles.get_vehicle(vehicle_id), True)}

    @app.post("/api/vehicles/{vehicle_id}/drivers/")
    async def assign_driver(vehicle_id: int, request: Request, user=Depends(current_user)):
        return await driver_request(vehicle_id, request, user, False)

    @app.patch("/api/vehicles/{vehicle_id}/drivers/current/")
    async def correct_driver(vehicle_id: int, request: Request, user=Depends(current_user)):
        return await driver_request(vehicle_id, request, user, True)

    @app.post("/api/vehicles/{vehicle_id}/drivers/{assignment_id}/end/")
    async def end_driver(
        vehicle_id: int, assignment_id: int, request: Request, user=Depends(current_user)
    ):
        require_csrf(request)
        payload = await read_json_body(
            request,
            size_limit=1024,
            too_large_message="The end-date form is too large.",
            invalid_message="Invalid end-date form.",
        )
        if not isinstance(payload, dict) or set(payload) != {"last_worked_on"}:
            raise DomainError("Provide the last working date only.")
        await run_in_threadpool(
            app.state.drivers.end, vehicle_id, assignment_id, payload["last_worked_on"], user
        )
        return {"vehicle": vehicle_payload(app.state.vehicles.get_vehicle(vehicle_id), True)}

    @app.get("/api/vehicles/{vehicle_id}/drivers/{assignment_id}/attachments/")
    def driver_attachments(vehicle_id: int, assignment_id: int, user=Depends(current_user)):
        return {
            "attachments": [
                attachment_payload(item)
                for item in app.state.vehicles.driver_attachments(vehicle_id, assignment_id)
            ]
        }

    @app.post("/api/vehicles/{vehicle_id}/drivers/{assignment_id}/attachments/")
    async def upload_driver_attachment(
        vehicle_id: int, assignment_id: int, request: Request, user=Depends(current_user)
    ):
        return await upload_request(app, vehicle_id, request, False, user, assignment_id)

    @app.delete(
        "/api/vehicles/{vehicle_id}/drivers/{assignment_id}/attachments/{attachment_id}/",
        status_code=204,
    )
    def delete_driver_attachment(
        vehicle_id: int,
        assignment_id: int,
        attachment_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        require_csrf(request)
        app.state.vehicles.delete_attachment(
            vehicle_id, attachment_id, actor=user, assignment_id=assignment_id
        )
        return Response(status_code=204)

    @app.patch("/api/vehicles/{vehicle_id}/drivers/{assignment_id}/attachments/{attachment_id}/")
    async def rename_driver_attachment(
        vehicle_id: int,
        assignment_id: int,
        attachment_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        return await rename_attachment_request(
            app, vehicle_id, attachment_id, request, user, assignment_id
        )

    @app.api_route(
        "/api/vehicles/{vehicle_id}/drivers/{assignment_id}/attachments/{attachment_id}/download/",
        methods=["GET", "HEAD"],
    )
    def download_driver_attachment(
        vehicle_id: int, assignment_id: int, attachment_id: int, user=Depends(current_user)
    ):
        item = app.state.vehicles.get_attachment(
            vehicle_id, attachment_id, assignment_id=assignment_id
        )
        return file_response(app, item.storage_key, item.original_name, False)

    @app.api_route(
        "/api/vehicles/{vehicle_id}/drivers/{assignment_id}/attachments/{attachment_id}/preview/",
        methods=["GET", "HEAD"],
    )
    def preview_driver_attachment(
        vehicle_id: int,
        assignment_id: int,
        attachment_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        return preview_item(
            app,
            app.state.vehicles.get_attachment(
                vehicle_id, attachment_id, assignment_id=assignment_id
            ),
            request,
            user,
        )
