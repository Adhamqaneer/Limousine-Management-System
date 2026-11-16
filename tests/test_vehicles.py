from dataclasses import replace
from datetime import datetime, timezone

from unittest import TestCase as SimpleTestCase

from limousine.application.vehicles import VehicleService
from limousine.domain.vehicles import Attachment, DomainError, NotFound, Vehicle, normalize_plate_number


class MemoryVehicleRepository:
    """Test adapter only. The application never selects this for runtime use."""

    def __init__(self):
        self.vehicles = {}
        self.attachments = {}
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def list_vehicles(self):
        return list(reversed(list(self.vehicles.values())))

    def get_vehicle(self, vehicle_id):
        try:
            vehicle = self.vehicles[vehicle_id]
        except KeyError as error:
            raise NotFound("Vehicle not found.") from error
        attachments = tuple(item for item in self.attachments.values() if item.vehicle_id == vehicle_id)
        return replace(vehicle, attachments=attachments)

    def create_vehicle(self, plate_number, **fields):
        vehicle = Vehicle(len(self.vehicles) + 1, plate_number, self.now, **fields)
        self.vehicles[vehicle.id] = vehicle
        return vehicle

    def update_vehicle(self, vehicle_id, **fields):
        vehicle = replace(self.get_vehicle(vehicle_id), **fields)
        self.vehicles[vehicle_id] = vehicle
        return vehicle

    def add_attachment(self, vehicle_id, **metadata):
        attachment = Attachment(len(self.attachments) + 1, vehicle_id=vehicle_id, created_at=self.now, **metadata)
        self.attachments[attachment.id] = attachment
        return attachment

    def get_attachment(self, vehicle_id, attachment_id):
        attachment = self.attachments.get(attachment_id)
        if not attachment or attachment.vehicle_id != vehicle_id:
            raise NotFound("Attachment not found for this vehicle.")
        return attachment


class PlateNumberTests(SimpleTestCase):
    def test_preserves_flexible_formats_and_leading_zeroes(self):
        self.assertEqual(normalize_plate_number("  00123 - أ  "), "00123 - أ")

    def test_rejects_empty_nontext_and_multiline_values(self):
        for value in ("", "   ", None, 123, "12\n34", "12\t34", "\x00123"):
            with self.subTest(value=value), self.assertRaises(DomainError):
                normalize_plate_number(value)

    def test_enforces_length_without_inventing_a_plate_format(self):
        self.assertEqual(normalize_plate_number("أ" * 64), "أ" * 64)
        with self.assertRaises(DomainError):
            normalize_plate_number("أ" * 65)


class VehicleUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.repository = MemoryVehicleRepository()
        self.service = VehicleService(self.repository)

    def test_new_vehicle_follows_existing_vehicles_even_when_timestamps_match(self):
        first = self.service.create_vehicle(" 001 ", "Sedan")
        second = self.service.create_vehicle("002", "Sedan")
        self.assertEqual([item.id for item in self.service.list_vehicles()], [first.id, second.id])
        self.assertEqual(first.plate_number, "001")

    def test_edit_preserves_vehicle_identity_creation_date_and_order(self):
        first = self.service.create_vehicle("001", "Sedan")
        self.service.create_vehicle("002", "Sedan")
        edited = self.service.update_vehicle(first.id, plate_number=" 003 ")
        self.assertEqual((edited.id, edited.created_at, edited.plate_number), (first.id, first.created_at, "003"))
        self.assertEqual([item.id for item in self.service.list_vehicles()], [1, 2])

    def test_invalid_input_does_not_create_or_modify_a_record(self):
        vehicle = self.service.create_vehicle("001", "Sedan")
        with self.assertRaises(DomainError):
            self.service.create_vehicle("", "Sedan")
        with self.assertRaises(DomainError):
            self.service.update_vehicle(vehicle.id, plate_number=" ")
        self.assertEqual(len(self.repository.vehicles), 1)
        self.assertEqual(self.service.get_vehicle(vehicle.id).plate_number, "001")

    def test_missing_vehicle_is_reported_without_creating_an_attachment(self):
        with self.assertRaises(NotFound):
            self.service.add_attachment(999, storage_key="key", original_name="photo.jpg", kind="image", size=10)
        self.assertEqual(self.repository.attachments, {})

    def test_attachments_are_returned_only_for_their_vehicle(self):
        first = self.service.create_vehicle("001", "Sedan")
        second = self.service.create_vehicle("002", "Sedan")
        attachment = self.service.add_attachment(first.id, storage_key="opaque-key", original_name=" photo.jpg ", kind="image", size=100)
        self.assertEqual(self.service.get_vehicle(first.id).attachments, (attachment,))
        self.assertEqual(self.service.get_vehicle(second.id).attachments, ())
        self.assertEqual(self.service.get_attachment(first.id, attachment.id).original_name, "photo.jpg")
        with self.assertRaises(NotFound):
            self.service.get_attachment(second.id, attachment.id)

    def test_invalid_attachment_metadata_is_not_saved(self):
        vehicle = self.service.create_vehicle("001", "Sedan")
        valid = dict(storage_key="opaque-key", original_name="file.pdf", kind="file", size=100)
        for invalid in ({"storage_key": ""}, {"original_name": " "}, {"kind": "script"}, {"size": 0}, {"size": True}):
            with self.subTest(invalid=invalid), self.assertRaises(DomainError):
                self.service.add_attachment(vehicle.id, **(valid | invalid))
        self.assertEqual(self.repository.attachments, {})

    def test_agreed_text_fields_preserve_zeroes_and_partial_edits(self):
        car = self.service.create_vehicle("001", "  Sedan  ", chassis_number=" 0007 ", manufacture_year="٢٠٢٠")
        edited = self.service.update_vehicle(car.id, driver_name="  أحمد  ")
        self.assertEqual((edited.vehicle_type, edited.chassis_number, edited.manufacture_year, edited.driver_name),
                         ("Sedan", "0007", "٢٠٢٠", "أحمد"))

    def test_type_is_required_and_other_fields_must_be_single_line_text(self):
        for fields in ({"vehicle_type": " "}, {"vehicle_type": "Sedan", "driver_name": "a\nb"},
                       {"vehicle_type": "Sedan", "manufacture_year": 2020},
                       {"vehicle_type": "Sedan", "chassis_number": "x" * 121}):
            with self.subTest(fields=fields), self.assertRaises(DomainError):
                self.service.create_vehicle("001", **fields)
        self.assertEqual(self.repository.vehicles, {})
