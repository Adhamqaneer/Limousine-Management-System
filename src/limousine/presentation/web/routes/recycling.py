"""Recycling pages and API endpoints."""

from fastapi import Depends, Request
from starlette.responses import Response

from limousine.domain.vehicles import DomainError

from ..rendering import render_page
from ..security import current_user, require_csrf


def register_routes(app):
    @app.delete("/api/vehicles/{vehicle_id}/", status_code=204)
    def delete_vehicle(vehicle_id: int, request: Request, user=Depends(current_user)):
        require_csrf(request)
        app.state.recycling.delete_vehicle(vehicle_id, user)
        return Response(status_code=204)

    @app.get("/recycle-bin/")
    def recycle_bin(request: Request, user=Depends(current_user)):
        return render_page(request, "recycle_bin.html", user=user)

    @app.get("/api/recycle-bin/")
    def deleted_items(user=Depends(current_user)):
        return {"items": app.state.recycling.list_deleted(user)}

    @app.post("/api/recycle-bin/{kind}/{item_id}/restore/", status_code=204)
    def restore_item(kind: str, item_id: int, request: Request, user=Depends(current_user)):
        require_csrf(request)
        app.state.recycling.restore_item(kind, item_id, user)
        return Response(status_code=204)

    @app.get("/api/activity/")
    def activity(before: int | None = None, user=Depends(current_user)):
        if before is not None and before < 1:
            raise DomainError("Invalid activity cursor.")
        return {"events": app.state.recycling.list_activity(user, before)}
