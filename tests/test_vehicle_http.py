import io
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch

import psycopg
from fastapi.testclient import TestClient
from PIL import Image

from limousine.application.vehicles import VehicleService
from limousine.config.runtime import Settings
from limousine.domain.vehicles import (
    Attachment,
    NotFound,
    Vehicle,
    VehicleCover,
    VehicleNumberInUse,
)
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import OPERATOR

STAMP = datetime.now(timezone.utc)


def photo():
    stream = io.BytesIO()
    Image.new(
        "RGB",
        (2, 2),
        "white",
    ).save(
        stream,
        "PNG",
    )
    return stream.getvalue()


class VehicleHttpTests(TestCase):
    def test_occupied_category_is_rejected_before_writing_image_or_file(self):
        from dataclasses import replace

        existing = Attachment(
            7,
            1,
            "vehicles/" + "a" * 32 + ".png",
            "license.png",
            "image",
            10,
            STAMP,
            category_id=13,
        )
        self.service.get_vehicle.return_value = replace(
            self.car,
            attachments=(existing,),
        )
        self.app.state.categories = MagicMock()
        self.app.state.categories.get.return_value = {"id": 13, "is_other": False}
        for name, content in [("new.png", photo()), ("new.txt", b"original document")]:
            with patch.object(
                self.app.state.store,
                "save",
            ) as save:
                response = self.client.post(
                    "/api/vehicles/1/attachments/",
                    files={"file": (name, content)},
                    data={"category_id": "13"},
                    headers=self.headers,
                )
                self.assertEqual(
                    response.status_code,
                    409,
                )
                self.assertEqual(
                    response.json()["error"]["code"],
                    "category_in_use",
                )
                save.assert_not_called()
        self.service.add_attachment.assert_not_called()

    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.app = create_app(Settings(media_root=Path(self.directory.name)))
        self.app.dependency_overrides[current_user] = lambda: OPERATOR
        self.service = MagicMock()
        self.app.state.vehicles = self.service
        self.app.state.cleanup = MagicMock()
        self.car = Vehicle(
            1,
            "050-001",
            STAMP,
            vehicle_type="Sedan",
        )
        self.service.get_vehicle.return_value = self.car
        self.service.create_vehicle.return_value = self.car
        self.service.update_vehicle.return_value = self.car
        self.client = TestClient(self.app)
        self.client.get("/login/")
        self.headers = {"X-CSRFToken": self.client.cookies["csrftoken"]}

    def test_fixed_fields_create_patch_and_private_serialization(self):
        response = self.client.post(
            "/api/vehicles/",
            json={"plate_number": "050-001", "vehicle_type": "Sedan"},
            headers=self.headers,
        )
        self.assertEqual(
            response.status_code,
            201,
        )
        self.client.patch(
            "/api/vehicles/1/",
            json={"owner_name": "Owner"},
            headers=self.headers,
        )
        self.service.create_vehicle.assert_called_once_with(
            plate_number="050-001",
            vehicle_type="Sedan",
            actor=OPERATOR,
        )
        self.service.update_vehicle.assert_called_once_with(
            1,
            owner_name="Owner",
        )
        self.assertNotIn(
            "storage_key",
            response.text,
        )

    def test_owner_and_driver_contact_fields_are_adapted_and_serialized(self):
        from dataclasses import replace

        fields = dict(
            owner_name="Adham qaneer",
            owner_phone="0079",
            chassis_number="JT001a",
        )
        self.service.update_vehicle.return_value = replace(
            self.car,
            **fields,
        )
        response = self.client.patch(
            "/api/vehicles/1/",
            json=fields,
            headers=self.headers,
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.service.update_vehicle.assert_called_once_with(
            1,
            **fields,
        )
        for name, value in fields.items():
            self.assertEqual(
                response.json()["vehicle"][name],
                value,
            )

    def test_duplicate_vehicle_number_returns_a_conflict_on_create_and_edit(self):
        self.service.create_vehicle.side_effect = VehicleNumberInUse("Number already exists.")
        self.service.update_vehicle.side_effect = VehicleNumberInUse("Number already exists.")
        for method, path, data in (
            (
                self.client.post,
                "/api/vehicles/",
                {"plate_number": "050-001", "vehicle_type": "Sedan"},
            ),
            (self.client.patch, "/api/vehicles/1/", {"plate_number": "050-001"}),
        ):
            with self.subTest(path=path):
                response = method(
                    path,
                    json=data,
                    headers=self.headers,
                )
                self.assertEqual(
                    response.status_code,
                    409,
                )
                self.assertEqual(
                    response.json()["error"]["code"],
                    "vehicle_number_in_use",
                )

    def test_vehicle_number_without_hyphen_is_rejected_on_create_and_edit(self):
        repository = MagicMock()
        self.app.state.vehicles = VehicleService(repository)
        created = self.client.post(
            "/api/vehicles/",
            json={"plate_number": "5076523", "vehicle_type": "Sedan"},
            headers=self.headers,
        )
        updated = self.client.patch(
            "/api/vehicles/1/",
            json={"plate_number": "5076523"},
            headers=self.headers,
        )
        self.assertEqual(
            created.status_code,
            400,
        )
        self.assertEqual(
            updated.status_code,
            400,
        )
        repository.create_vehicle.assert_not_called()
        repository.update_vehicle.assert_not_called()

    def test_detail_fields_follow_agreed_order_and_text_storage(self):
        html = self.client.get("/").text
        names = [
            "plate_number",
            "owner_name",
            "driver_name",
            "vehicle_type",
            "manufacture_year",
            "chassis_number",
            "owner_phone",
            "driver_phone",
        ]
        form = html.split(
            'id="vehicle-information-form"',
            1,
        )[1].split(
            "</form>",
            1,
        )[0]
        self.assertEqual(
            sorted(
                names,
                key=lambda name: form.index('name="' + name + '"'),
            ),
            names,
        )
        self.assertNotIn(
            'type="number"',
            form,
        )
        self.assertIn(
            "/static/web/vehicle-validation.js",
            html,
        )

    def test_home_contains_only_the_three_agreed_filter_controls(self):
        html = self.client.get("/").text
        section = html.split(
            'id="vehicle-filters"',
            1,
        )[1].split(
            "</fieldset>",
            1,
        )[0]
        self.assertEqual(
            section.count("<select "),
            3,
        )
        for name in ("filter-owner", "filter-model", "filter-type"):
            self.assertIn(
                'id="' + name + '"',
                section,
            )
        self.assertIn(
            'id="clear-filters"',
            section,
        )
        self.assertIn(
            "/static/web/vehicle-filters.js",
            html,
        )
        self.assertIn(
            '<details class="filter-popover" id="filter-popover">',
            html,
        )
        self.assertIn(
            'id="print-results" disabled',
            html,
        )
        self.assertIn(
            'list="owner-suggestions"',
            html,
        )
        self.assertIn(
            '<datalist id="owner-suggestions">',
            html,
        )

    def test_invalid_body_csrf_and_database_errors(self):
        self.assertEqual(
            self.client.post(
                "/api/vehicles/",
                json={"plate_number": "001"},
            ).status_code,
            403,
        )
        for body in ("[]", "{broken", '{"plate_number":"001","extra":"no"}'):
            self.assertEqual(
                self.client.post(
                    "/api/vehicles/",
                    content=body,
                    headers={**self.headers, "Content-Type": "application/json"},
                ).status_code,
                400,
            )
        self.service.list_vehicles.side_effect = psycopg.OperationalError("private-secret")
        response = self.client.get("/api/vehicles/")
        self.assertEqual(
            response.status_code,
            503,
        )
        self.assertNotIn(
            "private-secret",
            response.text,
        )

    def test_gallery_is_independent_of_cover(self):
        item = Attachment(
            1,
            1,
            "private.png",
            "photo.png",
            "image",
            20,
            STAMP,
        )
        self.service.list_vehicles.return_value = [
            Vehicle(
                1,
                "001",
                STAMP,
                (item,),
                cover=None,
            )
        ]
        self.assertIsNone(self.client.get("/api/vehicles/").json()["vehicles"][0]["cover_url"])
        self.service.list_vehicles.return_value = [
            Vehicle(
                1,
                "001",
                STAMP,
                cover=VehicleCover(
                    1,
                    "key",
                    "cover.png",
                    20,
                ),
            )
        ]
        self.assertEqual(
            self.client.get("/api/vehicles/").json()["vehicles"][0]["cover_url"],
            "/api/vehicles/1/cover/",
        )

    def test_upload_cleanup_on_failed_metadata_and_invalid_files(self):
        self.service.add_attachment.side_effect = psycopg.OperationalError("redacted")
        response = self.client.post(
            "/api/vehicles/1/attachments/",
            files={"file": ("car.png", photo(), "image/png")},
            headers=self.headers,
        )
        self.assertEqual(
            response.status_code,
            503,
        )
        # The cleanup adapter must check committed references before unlinking.
        self.app.state.cleanup.discard.assert_called_once()
        response = self.client.post(
            "/api/vehicles/1/cover/",
            files={"file": ("file.txt", b"hello", "text/plain")},
            headers=self.headers,
        )
        self.assertEqual(
            response.status_code,
            400,
        )

    def test_preview_download_and_ownership(self):
        from tests.uploads import SimpleUploadedFile

        for filename, content, mime in (
            ("car.png", photo(), "image/png"),
            ("text.txt", b"<script>hello</script>", "text/plain; charset=utf-8"),
            ("test.pdf", b"%PDF-1.7\n%%EOF", "application/pdf"),
        ):
            stored = self.app.state.store.save(
                SimpleUploadedFile(
                    filename,
                    content,
                )
            )
            self.service.get_attachment.return_value = Attachment(
                1,
                1,
                stored.storage_key,
                filename,
                stored.kind,
                len(content),
                STAMP,
            )
            response = self.client.get("/api/vehicles/1/attachments/1/preview/")
            self.assertEqual(
                response.status_code,
                200,
            )
            self.assertEqual(
                response.content,
                content,
            )
            self.assertEqual(
                response.headers["content-type"],
                mime,
            )
            self.assertIn(
                "inline",
                response.headers["content-disposition"],
            )
            download = self.client.get("/api/vehicles/1/attachments/1/download/")
            self.assertIn(
                "attachment",
                download.headers["content-disposition"],
            )
        self.service.get_attachment.side_effect = NotFound()
        self.assertEqual(
            self.client.get("/api/vehicles/2/attachments/1/preview/").status_code,
            404,
        )

    def test_jinja_pages_and_csrf_cookie_are_stable_between_tabs(self):
        response = self.client.get("/")
        self.assertIn(
            "H SPACE | Vehicles",
            response.text,
        )
        self.assertNotIn(
            'href="/users/"',
            response.text,
        )
        self.assertEqual(
            self.client.cookies["csrftoken"],
            self.headers["X-CSRFToken"],
        )
        self.assertEqual(
            self.client.get("/recycle-bin/").status_code,
            200,
        )

    def test_delete_requires_csrf_and_does_not_accept_get(self):
        for url in ("/api/vehicles/1/attachments/2/", "/api/vehicles/1/cover/"):
            self.assertEqual(
                self.client.delete(url).status_code,
                403,
            )
        self.service.delete_attachment.assert_not_called()
        self.service.delete_cover.assert_not_called()
        self.assertEqual(
            self.client.get("/api/vehicles/1/attachments/2/").status_code,
            405,
        )

    def test_delete_uses_vehicle_scope_actor_and_never_unlinks_retained_files(self):
        self.service.delete_attachment.return_value = "key-for-attachment"
        response = self.client.delete(
            "/api/vehicles/1/attachments/2/",
            headers=self.headers,
        )
        self.assertEqual(
            response.status_code,
            204,
        )
        self.service.delete_attachment.assert_called_once_with(
            1,
            2,
            actor=OPERATOR,
        )
        self.app.state.cleanup.process.assert_not_called()
        self.app.state.cleanup.reset_mock()
        self.service.delete_attachment.side_effect = NotFound()
        self.assertEqual(
            self.client.delete(
                "/api/vehicles/9/attachments/2/",
                headers=self.headers,
            ).status_code,
            404,
        )
        self.app.state.cleanup.process.assert_not_called()
        self.service.delete_attachment.side_effect = psycopg.OperationalError("private")
        response = self.client.delete(
            "/api/vehicles/1/attachments/2/",
            headers=self.headers,
        )
        self.assertEqual(
            response.status_code,
            503,
        )
        self.assertNotIn(
            "private",
            response.text,
        )
        self.app.state.cleanup.process.assert_not_called()

    def test_cover_removal_is_independent_and_retains_bytes(self):
        self.service.delete_cover.return_value = "old-cover"
        self.app.state.cleanup.process.return_value = False
        self.assertEqual(
            self.client.delete(
                "/api/vehicles/1/cover/",
                headers=self.headers,
            ).status_code,
            204,
        )
        self.service.delete_cover.assert_called_once_with(
            1,
            actor=OPERATOR,
        )
        self.service.delete_attachment.assert_not_called()
        self.app.state.cleanup.process.assert_not_called()

    def test_anonymous_cannot_delete(self):
        self.app.dependency_overrides.clear()
        for url in ("/api/vehicles/1/attachments/2/", "/api/vehicles/1/cover/"):
            self.assertEqual(
                self.client.delete(
                    url,
                    headers=self.headers,
                ).status_code,
                401,
            )
        self.service.delete_attachment.assert_not_called()
