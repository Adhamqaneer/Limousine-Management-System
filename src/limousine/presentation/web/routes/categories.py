"""Category names/aliases and attachment classification for all signed-in accounts."""

from fastapi import Depends, Request
from starlette.concurrency import run_in_threadpool

from limousine.domain.vehicles import DomainError
from limousine.infrastructure.office import attachment as office_attachment
from limousine.infrastructure.vehicle_repository import attachment as vehicle_attachment

from ..requests import read_json_body
from ..security import current_user, require_csrf
from ..serializers import attachment_payload


async def category_form(request, allowed, required):
    require_csrf(request)
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise DomainError("Send the category form as JSON.")
    payload = await read_json_body(
        request,
        size_limit=32768,
        too_large_message="The category form is too large.",
        invalid_message="Invalid category form.",
    )
    if (
        not isinstance(payload, dict)
        or set(payload) - set(allowed)
        or not set(required).issubset(payload)
    ):
        raise DomainError("Provide only the requested category fields.")
    return payload


def register_routes(app):
    @app.get("/api/attachment-categories/")
    def category_list(q: str = "", user=Depends(current_user)):
        return app.state.categories.list_categories(q)

    @app.post("/api/attachment-categories/")
    async def create_category(request: Request, user=Depends(current_user)):
        payload = await category_form(request, ("name", "allow_similar"), ("name",))
        row = await run_in_threadpool(
            app.state.categories.create, payload["name"], user, payload.get("allow_similar", False)
        )
        return {"category": {key: row[key] for key in ("id", "name", "code", "is_other")}}

    @app.post("/api/attachment-categories/{category_id}/aliases/")
    async def add_alias(category_id: int, request: Request, user=Depends(current_user)):
        payload = await category_form(request, ("name",), ("name",))
        row = await run_in_threadpool(
            app.state.categories.add_alias, category_id, payload["name"], user
        )
        return {"category": {key: row[key] for key in ("id", "name", "code", "is_other")}}

    @app.post("/api/attachment-categories/{category_id}/merge/")
    async def merge_category(category_id: int, request: Request, user=Depends(current_user)):
        payload = await category_form(request, ("target_id",), ("target_id",))
        row = await run_in_threadpool(
            app.state.categories.merge, category_id, payload["target_id"], user
        )
        return {"category": {key: row[key] for key in ("id", "name", "code", "is_other")}}

    async def classify(request, user, scope, attachment_id, vehicle_id=None, assignment_id=None):
        payload = await category_form(request, ("category_id",), ("category_id",))
        row = await run_in_threadpool(
            app.state.categories.classify,
            scope,
            attachment_id,
            payload["category_id"],
            user,
            vehicle_id,
            assignment_id,
        )
        item = office_attachment(row) if scope == "office" else vehicle_attachment(row)
        return {"attachment": attachment_payload(item)}

    @app.patch("/api/vehicles/{vehicle_id}/attachments/{attachment_id}/category/")
    async def classify_vehicle(
        vehicle_id: int, attachment_id: int, request: Request, user=Depends(current_user)
    ):
        return await classify(request, user, "vehicle", attachment_id, vehicle_id)

    @app.patch(
        "/api/vehicles/{vehicle_id}/drivers/{assignment_id}/attachments/{attachment_id}/category/"
    )
    async def classify_driver(
        vehicle_id: int,
        assignment_id: int,
        attachment_id: int,
        request: Request,
        user=Depends(current_user),
    ):
        return await classify(request, user, "vehicle", attachment_id, vehicle_id, assignment_id)

    @app.patch("/api/office/attachments/{attachment_id}/category/")
    async def classify_office(attachment_id: int, request: Request, user=Depends(current_user)):
        return await classify(request, user, "office", attachment_id)
