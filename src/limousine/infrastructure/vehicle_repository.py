"""Translate Django records into framework-independent vehicle data."""

from limousine.domain.vehicles import Attachment, NotFound, Vehicle
from limousine.infrastructure.django.models import AttachmentRecord, VehicleRecord


def _attachment(record: AttachmentRecord) -> Attachment:
    return Attachment(
        id=record.pk,
        vehicle_id=record.vehicle_id,
        storage_key=record.storage_key,
        original_name=record.original_name,
        kind=record.kind,
        size=record.size,
        created_at=record.created_at,
    )


def _vehicle(record: VehicleRecord) -> Vehicle:
    return Vehicle(
        id=record.pk,
        plate_number=record.plate_number,
        created_at=record.created_at,
        attachments=tuple(_attachment(attachment) for attachment in record.attachments.all()),
    )


class DjangoVehicleRepository:
    def list_vehicles(self) -> list[Vehicle]:
        records = VehicleRecord.objects.order_by("id").prefetch_related("attachments")
        return [_vehicle(record) for record in records]

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        try:
            record = VehicleRecord.objects.prefetch_related("attachments").get(pk=vehicle_id)
        except VehicleRecord.DoesNotExist as error:
            raise NotFound("Vehicle not found.") from error
        return _vehicle(record)

    def create_vehicle(self, plate_number: str) -> Vehicle:
        record = VehicleRecord.objects.create(plate_number=plate_number)
        return Vehicle(id=record.pk, plate_number=record.plate_number, created_at=record.created_at)

    def update_vehicle(self, vehicle_id: int, plate_number: str) -> Vehicle:
        updated = VehicleRecord.objects.filter(pk=vehicle_id).update(plate_number=plate_number)
        if not updated:
            raise NotFound("Vehicle not found.")
        return self.get_vehicle(vehicle_id)

    def add_attachment(
        self, vehicle_id: int, *, storage_key: str, original_name: str, kind: str, size: int
    ) -> Attachment:
        record = AttachmentRecord.objects.create(
            vehicle_id=vehicle_id,
            storage_key=storage_key,
            original_name=original_name,
            kind=kind,
            size=size,
        )
        return _attachment(record)

    def get_attachment(self, vehicle_id: int, attachment_id: int) -> Attachment:
        try:
            record = AttachmentRecord.objects.get(pk=attachment_id, vehicle_id=vehicle_id)
        except AttachmentRecord.DoesNotExist as error:
            raise NotFound("Attachment not found for this vehicle.") from error
        return _attachment(record)
