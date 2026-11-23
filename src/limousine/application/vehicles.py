"""The first vehicle use cases; persistence is supplied through a repository."""

from dataclasses import dataclass
from typing import Protocol

from limousine.domain.attachments import AttachmentNameConflict, renamed_attachment_name
from limousine.domain.recycling import require_actor
from limousine.domain.vehicles import (
    Attachment,
    DomainError,
    NotFound,
    Vehicle,
    VehicleCover,
    normalize_plate_number,
    normalize_vehicle_fields,
)


class VehicleRepository(Protocol):
    def list_vehicles(self) -> list[Vehicle]: ...
    def get_vehicle(
        self,
        vehicle_id: int,
    ) -> Vehicle: ...
    def create_vehicle(
        self,
        plate_number: str,
        *,
        actor=None,
        **fields: str,
    ) -> Vehicle: ...
    def update_vehicle(
        self,
        vehicle_id: int,
        **fields: str,
    ) -> Vehicle: ...
    def add_attachment(
        self,
        vehicle_id: int,
        *,
        storage_key: str,
        original_name: str,
        kind: str,
        size: int,
        actor=None,
        assignment_id=None,
        category_id=None,
    ) -> Attachment: ...
    def get_attachment(
        self,
        vehicle_id: int,
        attachment_id: int,
        *,
        assignment_id=None,
    ) -> Attachment: ...
    def driver_attachments(
        self,
        vehicle_id: int,
        assignment_id: int,
    ) -> list[Attachment]: ...
    def delete_attachment(
        self,
        vehicle_id: int,
        attachment_id: int,
        *,
        actor,
        assignment_id=None,
    ) -> None: ...
    def rename_attachment(
        self,
        vehicle_id: int,
        attachment_id: int,
        original_name: str,
        *,
        expected_name: str,
        actor,
        assignment_id=None,
    ) -> Attachment: ...
    def delete_cover(
        self,
        vehicle_id: int,
        *,
        actor,
    ) -> None: ...
    def replace_cover(
        self,
        cover: VehicleCover,
        *,
        actor,
    ) -> tuple[VehicleCover, None]: ...


@dataclass(frozen=True)
class AttachmentDownload:
    plate_number: str
    attachments: tuple[Attachment, ...]


class VehicleService:
    def __init__(
        self,
        repository: VehicleRepository,
    ):
        self.repository = repository

    def list_vehicles(self) -> list[Vehicle]:
        # The sequence of creation is the agreed display order. The id also
        # breaks ties when vehicles share a timestamp.
        return sorted(
            self.repository.list_vehicles(),
            key=lambda vehicle: vehicle.id,
        )

    def get_vehicle(
        self,
        vehicle_id: int,
    ) -> Vehicle:
        return self.repository.get_vehicle(vehicle_id)

    def prepare_attachment_download(
        self,
        vehicle_id: int,
        kind: str,
    ) -> AttachmentDownload:
        if kind not in ("image", "file"):
            raise DomainError("Choose photos or files for the download.")
        vehicle = self.repository.get_vehicle(vehicle_id)
        attachments = tuple(item for item in vehicle.attachments if item.kind == kind)
        if (
            not attachments
            or any(item.vehicle_id != vehicle_id for item in attachments)
        ):
            raise NotFound("No matching attachments exist for this vehicle.")
        return AttachmentDownload(
            vehicle.plate_number,
            attachments,
        )

    def create_vehicle(
        self,
        plate_number: str,
        vehicle_type: str,
        *,
        actor=None,
        **fields: str,
    ) -> Vehicle:
        return self.repository.create_vehicle(
            normalize_plate_number(plate_number),
            **normalize_vehicle_fields({"vehicle_type": vehicle_type, **fields}),
            **({"actor": actor} if actor else {}),
        )

    def update_vehicle(
        self,
        vehicle_id: int,
        **fields: str,
    ) -> Vehicle:
        if {"driver_name", "driver_phone"} & fields.keys():
            raise DomainError("Use Change driver or Correct current driver to preserve history.")
        if not fields:
            raise DomainError("Provide at least one vehicle field.")
        normalized = {}
        if "plate_number" in fields:
            normalized["plate_number"] = normalize_plate_number(fields.pop("plate_number"))
        normalized.update(normalize_vehicle_fields(fields))
        return self.repository.update_vehicle(
            vehicle_id,
            **normalized,
        )

    def add_attachment(
        self,
        vehicle_id: int,
        *,
        storage_key: str,
        original_name: str,
        kind: str,
        size: int,
        actor=None,
        assignment_id=None,
        category_id=None,
    ) -> Attachment:
        if assignment_id is not None:
            require_actor(actor)
        self.repository.get_vehicle(vehicle_id)
        if (
            not isinstance(
                storage_key,
                str,
            )
            or not storage_key.strip()
            or len(storage_key) > 500
        ):
            raise DomainError("The attachment storage key is invalid.")
        if (
            not isinstance(
                original_name,
                str,
            )
            or not original_name.strip()
            or len(original_name) > 255
        ):
            raise DomainError("The attachment name must contain between 1 and 255 characters.")
        if kind not in ("image", "file"):
            raise DomainError("The attachment type is invalid.")
        if (
            isinstance(
                size,
                bool,
            )
            or not isinstance(
                size,
                int,
            )
            or size <= 0
        ):
            raise DomainError("Choose a non-empty file.")
        return self.repository.add_attachment(
            vehicle_id,
            storage_key=storage_key,
            original_name=original_name.strip(),
            kind=kind,
            size=size,
            **({"actor": actor} if actor else {}),
            **({"category_id": category_id} if category_id is not None else {}),
            **({"assignment_id": assignment_id} if assignment_id is not None else {}),
        )

    def get_attachment(
        self,
        vehicle_id: int,
        attachment_id: int,
        *,
        assignment_id=None,
    ) -> Attachment:
        attachment = self.repository.get_attachment(
            vehicle_id,
            attachment_id,
            **({"assignment_id": assignment_id} if assignment_id is not None else {}),
        )
        if (
            attachment.vehicle_id != vehicle_id
            or attachment.driver_assignment_id != assignment_id
        ):
            raise NotFound("Attachment not found for this vehicle.")
        return attachment

    def driver_attachments(
        self,
        vehicle_id,
        assignment_id,
    ):
        return self.repository.driver_attachments(
            vehicle_id,
            assignment_id,
        )

    def get_cover(
        self,
        vehicle_id: int,
    ) -> VehicleCover:
        cover = self.repository.get_vehicle(vehicle_id).cover
        if cover is None:
            raise NotFound("This vehicle has no card photo.")
        return cover

    def delete_attachment(
        self,
        vehicle_id: int,
        attachment_id: int,
        *,
        actor,
        assignment_id=None,
    ):
        require_actor(actor)
        return self.repository.delete_attachment(
            vehicle_id,
            attachment_id,
            actor=actor,
            **({"assignment_id": assignment_id} if assignment_id is not None else {}),
        )

    def rename_attachment(
        self,
        vehicle_id,
        attachment_id,
        name,
        expected_name,
        *,
        actor,
        assignment_id=None,
    ):
        require_actor(actor)
        item = self.get_attachment(
            vehicle_id,
            attachment_id,
            assignment_id=assignment_id,
        )
        if expected_name != item.original_name:
            raise AttachmentNameConflict("The attachment name changed. Refresh and try again.")
        original_name = renamed_attachment_name(
            name,
            item.original_name,
        )
        return self.repository.rename_attachment(
            vehicle_id,
            attachment_id,
            original_name,
            expected_name=expected_name,
            actor=actor,
            **({"assignment_id": assignment_id} if assignment_id is not None else {}),
        )

    def delete_cover(
        self,
        vehicle_id: int,
        *,
        actor,
    ):
        require_actor(actor)
        return self.repository.delete_cover(
            vehicle_id,
            actor=actor,
        )

    def replace_cover(
        self,
        vehicle_id: int,
        *,
        storage_key: str,
        original_name: str,
        size: int,
        actor,
    ):
        require_actor(actor)
        self.repository.get_vehicle(vehicle_id)
        if (
            not isinstance(
                storage_key,
                str,
            )
            or not storage_key.strip()
            or len(storage_key) > 500
        ):
            raise DomainError("The card photo storage key is invalid.")
        if (
            not isinstance(
                original_name,
                str,
            )
            or not original_name.strip()
            or len(original_name) > 255
        ):
            raise DomainError("The card photo name is invalid.")
        if (
            isinstance(
                size,
                bool,
            )
            or not isinstance(
                size,
                int,
            )
            or size <= 0
        ):
            raise DomainError("Choose a non-empty photo.")
        return self.repository.replace_cover(
            VehicleCover(
                vehicle_id,
                storage_key,
                original_name.strip(),
                size,
            ),
            actor=actor,
        )
