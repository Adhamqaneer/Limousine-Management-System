"""HTTP adaptation for vehicle use cases; never substitutes another database."""

import json
import logging
from functools import wraps

from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.db import DatabaseError, InterfaceError
from django.http import FileResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from limousine.application.vehicles import VehicleService
from limousine.domain.vehicles import DomainError, NotFound
from limousine.infrastructure.attachments import AttachmentTooLarge, LocalAttachmentStore, MAX_ATTACHMENT_BYTES
from limousine.infrastructure.vehicle_repository import DjangoVehicleRepository

logger = logging.getLogger(__name__)


def get_vehicle_service():
    return VehicleService(DjangoVehicleRepository())


def error_response(code, message, status):
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def api_errors(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not settings.ORACLE_CONFIGURED:
            return error_response("storage_unavailable", "Oracle is not configured yet. Saving vehicles will be available after setup.", 503)
        try:
            return view(request, *args, **kwargs)
        except AttachmentTooLarge as error:
            return error_response("file_too_large", str(error), 413)
        except DomainError as error:
            return error_response("validation_error", str(error), 400)
        except NotFound:
            return error_response("not_found", "This vehicle or attachment could not be found.", 404)
        except (DatabaseError, InterfaceError):
            return error_response("storage_unavailable", "Vehicle storage is currently unavailable. Please try again later.", 503)
        except FileNotFoundError:
            return error_response("not_found", "The attachment file could not be found.", 404)
        except OSError:
            return error_response("storage_unavailable", "Attachment storage is currently unavailable. Please try again later.", 503)
        except RequestDataTooBig:
            return error_response("request_too_large", "The request is too large.", 413)
    return wrapped


def attachment_payload(attachment):
    base = f"/api/vehicles/{attachment.vehicle_id}/attachments/{attachment.id}"
    return {
        "id": attachment.id,
        "name": attachment.original_name,
        "kind": attachment.kind,
        "size": attachment.size,
        "uploaded_at": attachment.created_at.isoformat(),
        "download_url": f"{base}/download/",
        "preview_url": f"{base}/preview/" if attachment.kind == "image" else None,
    }


def vehicle_payload(vehicle, *, detailed=False):
    attachments = [attachment_payload(item) for item in vehicle.attachments]
    cover = next((item["preview_url"] for item in attachments if item["kind"] == "image"), None)
    result = {
        "id": vehicle.id, "plate_number": vehicle.plate_number,
        "created_at": vehicle.created_at.isoformat(),
        "attachment_count": len(attachments), "cover_url": cover,
    }
    if detailed:
        result["attachments"] = attachments
    return result


def plate_from_json(request):
    if request.content_type != "application/json":
        raise DomainError("Send vehicle details as JSON.")
    if len(request.body) > 8192:
        raise DomainError("The vehicle form is too large.")
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        raise DomainError("The vehicle form contains invalid JSON.") from None
    if not isinstance(payload, dict) or set(payload) != {"plate_number"}:
        raise DomainError("Provide the plate_number field only.")
    return payload["plate_number"]


@never_cache
@require_http_methods(["GET", "POST"])
@api_errors
def vehicles(request):
    service = get_vehicle_service()
    if request.method == "GET":
        return JsonResponse({"vehicles": [vehicle_payload(item) for item in service.list_vehicles()]})
    vehicle = service.create_vehicle(plate_from_json(request))
    return JsonResponse({"vehicle": vehicle_payload(vehicle, detailed=True)}, status=201)


@never_cache
@require_http_methods(["GET", "PATCH"])
@api_errors
def vehicle_detail(request, vehicle_id):
    service = get_vehicle_service()
    if request.method == "GET":
        vehicle = service.get_vehicle(vehicle_id)
    else:
        vehicle = service.update_vehicle(vehicle_id, plate_from_json(request))
    return JsonResponse({"vehicle": vehicle_payload(vehicle, detailed=True)})


@never_cache
@require_http_methods(["POST"])
@api_errors
def attachments(request, vehicle_id):
    try:
        length = int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return error_response("validation_error", "Invalid upload request.", 400)
    if length > MAX_ATTACHMENT_BYTES + 64 * 1024:
        raise AttachmentTooLarge("The file must be 10 MB or smaller.")
    service = get_vehicle_service()
    service.get_vehicle(vehicle_id)
    uploads = request.FILES.getlist("file")
    if set(request.FILES) != {"file"} or len(uploads) != 1:
        raise DomainError("Choose exactly one file to upload.")
    store = LocalAttachmentStore()
    try:
        stored = store.save(uploads[0])
    except AttachmentTooLarge:
        raise
    except DomainError as error:
        return error_response("invalid_file", str(error), 400)
    try:
        attachment = service.add_attachment(
            vehicle_id, storage_key=stored.storage_key, original_name=stored.original_name,
            kind=stored.kind, size=stored.size,
        )
    except Exception:
        # A failed metadata insert must not leave an unreachable upload behind.
        try:
            store.delete(stored.storage_key)
        except OSError:
            logger.warning("Failed to clean up an upload after a metadata failure.")
        raise
    return JsonResponse({"attachment": attachment_payload(attachment)}, status=201)


def attachment_response(request, vehicle_id, attachment_id, *, preview):
    attachment = get_vehicle_service().get_attachment(vehicle_id, attachment_id)
    store = LocalAttachmentStore()
    content_type = store.content_type(attachment.storage_key)
    if preview and (attachment.kind != "image" or not content_type.startswith("image/")):
        return error_response("not_found", "An image preview is not available for this file.", 404)
    response = FileResponse(
        store.open(attachment.storage_key), as_attachment=not preview,
        filename=attachment.original_name,
        content_type=content_type if preview else "application/octet-stream",
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "default-src 'none'; sandbox"
    response["Cache-Control"] = "private, no-store"
    return response


@never_cache
@require_http_methods(["GET", "HEAD"])
@api_errors
def attachment_download(request, vehicle_id, attachment_id):
    return attachment_response(request, vehicle_id, attachment_id, preview=False)


@never_cache
@require_http_methods(["GET", "HEAD"])
@api_errors
def attachment_preview(request, vehicle_id, attachment_id):
    return attachment_response(request, vehicle_id, attachment_id, preview=True)
