"""Read bounded JSON forms and validate vehicle field names."""

import json

from limousine.domain.vehicles import DomainError


async def read_json_body(
    request,
    *,
    size_limit,
    too_large_message,
    invalid_message,
):
    body = await request.body()
    if len(body) > size_limit:
        raise DomainError(too_large_message)
    try:
        return json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise DomainError(invalid_message) from None


async def vehicle_fields(
    request,
    creating=False,
):
    if (
        request.headers.get(
            "content-type",
            "",
        ).split(
            ";"
        )[0]
        != "application/json"
    ):
        raise DomainError("Send vehicle details as JSON.")
    payload = await read_json_body(
        request,
        size_limit=8192,
        too_large_message="The vehicle form is too large.",
        invalid_message="Invalid JSON.",
    )
    allowed = {
        "plate_number",
        "vehicle_type",
        "driver_name",
        "chassis_number",
        "manufacture_year",
        "owner_name",
        "owner_phone",
        "driver_phone",
    }
    if (
        not isinstance(
            payload,
            dict,
        )
        or not payload
        or set(payload) - allowed
    ):
        raise DomainError("Provide only the agreed vehicle fields.")
    if (
        creating
        and not {"plate_number", "vehicle_type"}.issubset(payload)
    ):
        raise DomainError("Provide vehicle type and plate number.")
    return payload
