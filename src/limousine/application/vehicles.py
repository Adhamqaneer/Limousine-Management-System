"""The first vehicle use cases; persistence is supplied through a repository."""

from typing import Protocol
from limousine.domain.recycling import require_actor

from limousine.domain.vehicles import Attachment, DomainError, NotFound, Vehicle, VehicleCover, normalize_plate_number, normalize_vehicle_fields


class VehicleRepository(Protocol):
    def list_vehicles(self) -> list[Vehicle]: ...
    def get_vehicle(self, vehicle_id: int) -> Vehicle: ...
    def create_vehicle(self, plate_number: str, *, actor=None, **fields: str) -> Vehicle: ...
    def update_vehicle(self, vehicle_id: int, **fields: str) -> Vehicle: ...
    def add_attachment(
        self, vehicle_id: int, *, storage_key: str, original_name: str, kind: str, size: int, actor=None
    ) -> Attachment: ...
    def get_attachment(self, vehicle_id: int, attachment_id: int) -> Attachment: ...
    def delete_attachment(self, vehicle_id: int, attachment_id: int, *, actor) -> None: ...
    def delete_cover(self, vehicle_id: int, *, actor) -> None: ...
    def replace_cover(self, cover: VehicleCover, *, actor) -> tuple[VehicleCover, None]: ...


class VehicleService:
    def __init__(self, repository: VehicleRepository):
        self.repository = repository

    def list_vehicles(self) -> list[Vehicle]:
        # The sequence of creation is the agreed display order. The id also
        # breaks ties when vehicles share a timestamp.
        return sorted(self.repository.list_vehicles(), key=lambda vehicle: vehicle.id)

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        return self.repository.get_vehicle(vehicle_id)

    def create_vehicle(self, plate_number: str, vehicle_type: str, *, actor=None, **fields: str) -> Vehicle:
        return self.repository.create_vehicle(
            normalize_plate_number(plate_number),
            **normalize_vehicle_fields({"vehicle_type": vehicle_type, **fields}),
            **({'actor': actor} if actor else {}),
        )

    def update_vehicle(self, vehicle_id: int, **fields: str) -> Vehicle:
        if {'driver_name','driver_phone'} & fields.keys():
            raise DomainError('Use Change driver or Correct current driver to preserve history.')
        if not fields:
            raise DomainError("Provide at least one vehicle field.")
        normalized = {}
        if "plate_number" in fields:
            normalized["plate_number"] = normalize_plate_number(fields.pop("plate_number"))
        normalized.update(normalize_vehicle_fields(fields))
        return self.repository.update_vehicle(vehicle_id, **normalized)

    def add_attachment(
        self, vehicle_id: int, *, storage_key: str, original_name: str, kind: str, size: int, actor=None
    ) -> Attachment:
        self.repository.get_vehicle(vehicle_id)
        if not isinstance(storage_key, str) or not storage_key.strip() or len(storage_key) > 500:
            raise DomainError("The attachment storage key is invalid.")
        if not isinstance(original_name, str) or not original_name.strip() or len(original_name) > 255:
            raise DomainError("The attachment name must contain between 1 and 255 characters.")
        if kind not in ("image", "file"):
            raise DomainError("The attachment type is invalid.")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise DomainError("Choose a non-empty file.")
        return self.repository.add_attachment(
            vehicle_id,
            storage_key=storage_key,
            original_name=original_name.strip(),
            kind=kind,
            size=size,
            **({'actor': actor} if actor else {}),
        )

    def get_attachment(self, vehicle_id: int, attachment_id: int) -> Attachment:
        attachment = self.repository.get_attachment(vehicle_id, attachment_id)
        if attachment.vehicle_id != vehicle_id:
            raise NotFound("Attachment not found for this vehicle.")
        return attachment

    def get_cover(self, vehicle_id: int) -> VehicleCover:
        cover = self.repository.get_vehicle(vehicle_id).cover
        if cover is None:
            raise NotFound("This vehicle has no card photo.")
        return cover

    def delete_attachment(self, vehicle_id: int, attachment_id: int, *, actor):
        require_actor(actor)
        return self.repository.delete_attachment(vehicle_id, attachment_id, actor=actor)

    def delete_cover(self, vehicle_id: int, *, actor):
        require_actor(actor)
        return self.repository.delete_cover(vehicle_id, actor=actor)

    def replace_cover(self, vehicle_id: int, *, storage_key: str, original_name: str, size: int, actor):
        require_actor(actor)
        self.repository.get_vehicle(vehicle_id)
        if not isinstance(storage_key, str) or not storage_key.strip() or len(storage_key) > 500:
            raise DomainError("The card photo storage key is invalid.")
        if not isinstance(original_name, str) or not original_name.strip() or len(original_name) > 255:
            raise DomainError("The card photo name is invalid.")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise DomainError("Choose a non-empty photo.")
        return self.repository.replace_cover(VehicleCover(vehicle_id, storage_key, original_name.strip(), size), actor=actor)
