import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from urllib.parse import quote
from zipfile import ZipFile

from fastapi.testclient import TestClient

from limousine.application.vehicles import VehicleService
from limousine.config.runtime import Settings
from limousine.domain.attachments import AttachmentNameError, renamed_attachment_name
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import OPERATOR
from tests.test_vehicle_http import photo
from tests.test_vehicles import MemoryVehicleRepository
from tests.uploads import SimpleUploadedFile


class AttachmentRenameTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.app = create_app(Settings(media_root=Path(directory.name)))
        self.repository = MemoryVehicleRepository()
        self.service = self.app.state.vehicles = VehicleService(self.repository)
        self.car = self.service.create_vehicle(
            "050-001",
            "Camry",
        )
        self.items, self.contents = [], [photo(), b"original document 00123"]
        for name, content in zip(
            ["old.PNG", "old.txt"],
            self.contents,
        ):
            stored = self.app.state.store.save(
                SimpleUploadedFile(
                    name,
                    content,
                )
            )
            self.items.append(
                self.service.add_attachment(
                    self.car.id,
                    **vars(stored),
                )
            )
        self.app.dependency_overrides[current_user] = lambda: OPERATOR
        self.client = TestClient(self.app)
        self.client.get("/login/")
        self.headers = {"X-CSRFToken": self.client.cookies["csrftoken"]}

    def url(
        self,
        index=0,
        vehicle_id=1,
    ):
        return f"/api/vehicles/{vehicle_id}/attachments/{self.items[index].id}/"

    def test_name_rules_preserve_exact_extension_and_reject_unsafe_names(self):
        self.assertEqual(
            renamed_attachment_name(
                " صورة جديدة ",
                "old.PNG",
            ),
            "صورة جديدة.PNG",
        )
        self.assertEqual(
            renamed_attachment_name(
                "version.2",
                "old.txt",
            ),
            "version.2.txt",
        )
        for name in [
            "",
            "..",
            "a/b",
            r"a\b",
            "bad:one",
            "bad\nname",
            "a\u202eb",
            "CON",
            "LPT1",
            "trailing.",
            "a" * 177,
            123,
        ]:
            with self.subTest(name=name), self.assertRaises(AttachmentNameError):
                renamed_attachment_name(
                    name,
                    "old.PNG",
                )

    def test_member_rename_changes_display_download_and_zip_without_changing_bytes(self):
        for index, stem in enumerate(["صورة جديدة", "New document"]):
            item = self.items[index]
            response = self.client.patch(
                self.url(index),
                json={"name": stem, "expected_name": item.original_name},
                headers=self.headers,
            )
            self.assertEqual(
                response.status_code,
                200,
            )
            expected = stem + Path(item.original_name).suffix
            self.assertEqual(
                response.json()["attachment"]["name"],
                expected,
            )
            self.assertNotIn(
                "storage_key",
                response.text,
            )
            updated = self.service.get_attachment(
                1,
                item.id,
            )
            self.assertEqual(
                (updated.id, updated.storage_key, updated.size, updated.created_at),
                (item.id, item.storage_key, item.size, item.created_at),
            )
            download = self.client.get(self.url(index) + "download/")
            self.assertEqual(
                download.content,
                self.contents[index],
            )
            self.assertIn(
                quote(expected),
                download.headers["content-disposition"],
            )
            scope = "photos" if index == 0 else "files"
            zipped = self.client.get(f"/api/vehicles/1/attachments/archive/{scope}/")
            with ZipFile(io.BytesIO(zipped.content)) as archive:
                self.assertEqual(
                    archive.namelist(),
                    [expected],
                )
                self.assertEqual(
                    archive.read(expected),
                    self.contents[index],
                )

    def test_stale_name_returns_conflict_and_keeps_latest_name(self):
        body = {"name": "First", "expected_name": "old.PNG"}
        self.assertEqual(
            self.client.patch(
                self.url(),
                json=body,
                headers=self.headers,
            ).status_code,
            200,
        )
        response = self.client.patch(
            self.url(),
            json={**body, "name": "Second"},
            headers=self.headers,
        )
        self.assertEqual(
            response.status_code,
            409,
        )
        self.assertEqual(
            response.json()["error"]["code"],
            "attachment_name_conflict",
        )
        self.assertEqual(
            self.service.get_attachment(
                1,
                self.items[0].id,
            ).original_name,
            "First.PNG",
        )

    def test_validation_csrf_authentication_and_wrong_vehicle(self):
        body = {"name": "New", "expected_name": "old.PNG"}
        self.assertEqual(
            self.client.patch(
                self.url(),
                json=body,
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.patch(
                self.url(vehicle_id=2),
                json=body,
                headers=self.headers,
            ).status_code,
            404,
        )
        for invalid in [
            {"name": "../bad", "expected_name": "old.PNG"},
            {**body, "storage_key": "forged"},
            {"name": "New"},
            {**body, "name": None},
        ]:
            self.assertEqual(
                self.client.patch(
                    self.url(),
                    json=invalid,
                    headers=self.headers,
                ).status_code,
                400,
            )
        self.app.dependency_overrides.clear()
        self.assertEqual(
            self.client.patch(
                self.url(),
                json=body,
                headers=self.headers,
            ).status_code,
            401,
        )
