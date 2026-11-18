"""Public JSON fields; private storage keys never leave the server."""

from limousine.domain.office import OfficeAttachment


def attachment_payload(item):
    if isinstance(item, OfficeAttachment):
        prefix = "/api/office"
    else:
        prefix = f"/api/vehicles/{item.vehicle_id}"
        if item.driver_assignment_id is not None:
            prefix += f"/drivers/{item.driver_assignment_id}"
    base = prefix + f"/attachments/{item.id}"
    return {
        "id": item.id,
        "name": item.original_name,
        "kind": item.kind,
        "size": item.size,
        "uploaded_at": item.created_at.isoformat(),
        "download_url": base + "/download/",
        "preview_url": base + "/preview/",
        "manage_url": base + "/",
    }


def vehicle_payload(item, detailed=False):
    payload = {
        "id": item.id,
        "plate_number": item.plate_number,
        "vehicle_type": item.vehicle_type,
        "driver_name": item.driver_name,
        "chassis_number": item.chassis_number,
        "manufacture_year": item.manufacture_year,
        "owner_name": item.owner_name,
        "owner_phone": item.owner_phone,
        "driver_phone": item.driver_phone,
        "created_at": item.created_at.isoformat(),
        "attachment_count": len(item.attachments),
        "cover_url": f"/api/vehicles/{item.id}/cover/" if item.cover else None,
    }
    if detailed:
        payload["attachments"] = [attachment_payload(file) for file in item.attachments]
    return payload


def user_payload(user):
    return {
        "id": str(user.id),
        "slot": user.slot,
        "username": user.username,
        "role": user.role.value,
        "is_active": user.is_active,
        "is_deleted": user.is_deleted,
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
    }
