import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.http import HttpResponse
from django.test import Client, SimpleTestCase, override_settings
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from limousine.domain.vehicles import Attachment, NotFound, Vehicle
from limousine.infrastructure.attachments import LocalAttachmentStore, MAX_ATTACHMENT_BYTES
from limousine.presentation.web import vehicle_views


@ensure_csrf_cookie
def csrf_seed(request):
    return HttpResponse("ok")


urlpatterns = [
    path("api/vehicles/", vehicle_views.vehicles),
    path("api/vehicles/<int:vehicle_id>/", vehicle_views.vehicle_detail),
    path("api/vehicles/<int:vehicle_id>/attachments/", vehicle_views.attachments),
    path("api/vehicles/<int:vehicle_id>/attachments/<int:attachment_id>/download/", vehicle_views.attachment_download),
    path("api/vehicles/<int:vehicle_id>/attachments/<int:attachment_id>/preview/", vehicle_views.attachment_preview),
    path("csrf-seed/", csrf_seed),
]

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/dYoAAAAASUVORK5CYII=")
STAMP = datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc)


@override_settings(ROOT_URLCONF=__name__, ORACLE_CONFIGURED=True)
class VehicleHttpTests(SimpleTestCase):
    def setUp(self):
        self.media = TemporaryDirectory(prefix="limousine-attachment-tests-")
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.service = MagicMock()
        self.factory = patch.object(vehicle_views, "get_vehicle_service", return_value=self.service)
        self.factory.start()
        self.addCleanup(self.factory.stop)
        self.vehicle = Vehicle(4, "12-34567", STAMP)
        self.service.get_vehicle.return_value = self.vehicle
        self.service.create_vehicle.return_value = self.vehicle
        self.service.update_vehicle.return_value = self.vehicle

    def test_list_exposes_safe_urls_and_first_image_cover(self):
        attachment = Attachment(6, 4, "vehicles/" + "a" * 32 + ".png", "صورة.png", "image", len(PNG), STAMP)
        self.service.list_vehicles.return_value = [Vehicle(4, "12-34567", STAMP, (attachment,))]
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, 200)
        item = response.json()["vehicles"][0]
        self.assertEqual(item["cover_url"], "/api/vehicles/4/attachments/6/preview/")
        self.assertEqual(item["attachment_count"], 1)
        self.assertNotIn("storage_key", response.content.decode())
        self.assertNotIn("attachments", item)
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_create_and_update_pass_the_fixed_plate_field(self):
        for method, url, status in (("post", "/api/vehicles/", 201), ("patch", "/api/vehicles/4/", 200)):
            response = getattr(self.client, method)(url, json.dumps({"plate_number": "12-34567"}), content_type="application/json")
            self.assertEqual(response.status_code, status)
            self.assertEqual(response.json()["vehicle"]["attachments"], [])
        self.service.create_vehicle.assert_called_once_with("12-34567")
        self.service.update_vehicle.assert_called_once_with(4, "12-34567")

    def test_invalid_json_and_unagreed_fields_are_rejected(self):
        for body in ("{broken", "[]", '{"plate_number":"12","free_text":"not agreed"}'):
            response = self.client.post("/api/vehicles/", body, content_type="application/json")
            self.assertEqual(response.status_code, 400)
        self.service.create_vehicle.assert_not_called()

    @override_settings(ORACLE_CONFIGURED=False)
    def test_unconfigured_oracle_never_uses_fake_storage(self):
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "storage_unavailable")
        self.service.list_vehicles.assert_not_called()

    def test_database_errors_are_redacted(self):
        self.service.list_vehicles.side_effect = DatabaseError("host=private password=secret")
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.content.decode())
        self.assertNotIn("secret", response.content.decode())

    def test_upload_stores_bytes_with_random_key_and_metadata_in_service(self):
        def record(vehicle_id, **data):
            return Attachment(8, vehicle_id, data["storage_key"], data["original_name"], data["kind"], data["size"], STAMP)
        self.service.add_attachment.side_effect = record
        upload = SimpleUploadedFile("../car.png", PNG, content_type="image/png")
        response = self.client.post("/api/vehicles/4/attachments/", {"file": upload})
        self.assertEqual(response.status_code, 201)
        attachment = response.json()["attachment"]
        self.assertEqual(attachment["kind"], "image")
        self.assertEqual(attachment["name"], "car.png")
        metadata = self.service.add_attachment.call_args.kwargs
        self.assertRegex(metadata["storage_key"], r"^vehicles/[0-9a-f]{32}\.png$")
        self.assertEqual((Path(self.media.name) / metadata["storage_key"]).read_bytes(), PNG)

    def test_failed_metadata_insert_removes_uploaded_bytes(self):
        self.service.add_attachment.side_effect = DatabaseError("unavailable")
        response = self.client.post("/api/vehicles/4/attachments/", {"file": SimpleUploadedFile("car.png", PNG)})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(list(Path(self.media.name).rglob("*.png")), [])

    def test_missing_vehicle_cannot_create_orphan_files(self):
        self.service.get_vehicle.side_effect = NotFound()
        response = self.client.post("/api/vehicles/99/attachments/", {"file": SimpleUploadedFile("car.png", PNG)})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(list(Path(self.media.name).rglob("*")), [])

    def test_active_files_and_mislabeled_images_are_rejected(self):
        for name in ("script.svg", "page.html", "tool.exe", "fake.png"):
            response = self.client.post("/api/vehicles/4/attachments/", {"file": SimpleUploadedFile(name, b"<script>alert(1)</script>")})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["error"]["code"], "invalid_file")
        self.service.add_attachment.assert_not_called()

    def test_oversized_upload_is_rejected_without_a_saved_file(self):
        response = self.client.post("/api/vehicles/4/attachments/", {"file": SimpleUploadedFile("large.txt", b"x" * (MAX_ATTACHMENT_BYTES + 1))})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(list(Path(self.media.name).rglob("*")), [])
        self.service.add_attachment.assert_not_called()

    def test_download_and_image_preview_have_separate_delivery_policies(self):
        store = LocalAttachmentStore()
        stored = store.save(SimpleUploadedFile("car.png", PNG))
        self.service.get_attachment.return_value = Attachment(8, 4, stored.storage_key, stored.original_name, stored.kind, stored.size, STAMP)
        for suffix in ("download", "preview"):
            response = self.client.get(f"/api/vehicles/4/attachments/8/{suffix}/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), PNG)
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertIn("no-store", response.headers["Cache-Control"])
            self.assertIn("attachment" if suffix == "download" else "inline", response.headers["Content-Disposition"])
            self.assertEqual(response.headers["Content-Type"], "application/octet-stream" if suffix == "download" else "image/png")
            response.close()

    def test_non_image_or_wrong_vehicle_attachment_has_no_preview(self):
        self.service.get_attachment.return_value = Attachment(8, 4, "vehicles/" + "a" * 32 + ".pdf", "record.pdf", "file", 20, STAMP)
        self.assertEqual(self.client.get("/api/vehicles/4/attachments/8/preview/").status_code, 404)
        self.service.get_attachment.side_effect = NotFound()
        self.assertEqual(self.client.get("/api/vehicles/99/attachments/8/download/").status_code, 404)
        self.service.get_attachment.assert_called_with(99, 8)

    def test_mutations_require_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/api/vehicles/", '{"plate_number":"12"}', content_type="application/json")
        self.assertEqual(response.status_code, 403)
        client.get("/csrf-seed/")
        response = client.post(
            "/api/vehicles/", '{"plate_number":"12"}', content_type="application/json",
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 201)

    def test_unsupported_methods_are_rejected(self):
        self.assertEqual(self.client.delete("/api/vehicles/4/").status_code, 405)
        self.assertEqual(self.client.get("/api/vehicles/4/attachments/").status_code, 405)
