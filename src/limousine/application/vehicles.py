"""The first vehicle use cases; persistence is supplied through a repository."""

from typing import Protocol

from limousine.domain.vehicles import Attachment, DomainError, NotFound, Vehicle, normalize_plate_number


class VehicleRepository(Protocol):
    def list_vehicles(self) -> list[Vehicle]: ...
    def get_vehicle(self, vehicle_id: int) -> Vehicle: ...
    def create_vehicle(self, plate_number: str) -> Vehicle: ...
    def update_vehicle(self, vehicle_id: int, plate_number: str) -> Vehicle: ...
    def add_attachment(
        self, vehicle_id: int, *, storage_key: str, original_name: str, kind: str, size: int
    ) -> Attachment: ...
    def get_attachment(self, vehicle_id: int, attachment_id: int) -> Attachment: ...


class VehicleService:
    def __init__(self, repository: VehicleRepository):
        self.repository = repository

    def list_vehicles(self) -> list[Vehicle]:
        # The sequence of creation is the agreed display order. The id also
        # breaks ties when vehicles share a timestamp.
        return sorted(self.repository.list_vehicles(), key=lambda vehicle: vehicle.id)

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        return self.repository.get_vehicle(vehicle_id)

    def create_vehicle(self, plate_number: str) -> Vehicle:
        return self.repository.create_vehicle(normalize_plate_number(plate_number))

    def update_vehicle(self, vehicle_id: int, plate_number: str) -> Vehicle:
        return self.repository.update_vehicle(vehicle_id, normalize_plate_number(plate_number))

    def add_attachment(
        self, vehicle_id: int, *, storage_key: str, original_name: str, kind: str, size: int
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
        )

    def get_attachment(self, vehicle_id: int, attachment_id: int) -> Attachment:
        attachment = self.repository.get_attachment(vehicle_id, attachment_id)
        if attachment.vehicle_id != vehicle_id:
            raise NotFound("Attachment not found for this vehicle.")
        return attachment
