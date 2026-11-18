import asyncio
import io
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

from fastapi.testclient import TestClient

from limousine.application.vehicles import VehicleService
from limousine.config.runtime import Settings
from limousine.domain.vehicles import Attachment, NotFound, Vehicle, VehicleCover
from limousine.infrastructure.attachment_archive import build_attachment_archive
from limousine.presentation.web.app import create_app
from limousine.presentation.web.downloads import ArchiveResponse
from limousine.presentation.web.security import current_user
from tests.test_accounts import MEMBER
from tests.test_vehicle_http import STAMP, photo
from tests.uploads import SimpleUploadedFile


class AttachmentArchiveTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.app = create_app(Settings(media_root=Path(directory.name)))
        self.app.dependency_overrides[current_user] = lambda: MEMBER
        self.repository = MagicMock()
        self.app.state.vehicles = VehicleService(self.repository)
        self.contents = [photo(), photo(), b"original text 00123", b"different original text"]
        self.items = []
        for index, (name, content) in enumerate(
            zip(["صورة.png", "صورة.png", "report.txt", "REPORT.txt"], self.contents), 1
        ):
            stored = self.app.state.store.save(SimpleUploadedFile(name, content))
            self.items.append(
                Attachment(index, 1, stored.storage_key, name, stored.kind, len(content), STAMP)
            )
        self.vehicle = Vehicle(
            1,
            "050-001",
            STAMP,
            tuple(self.items),
            cover=VehicleCover(1, self.items[0].storage_key, "card.png", len(self.contents[0])),
        )
        self.repository.get_vehicle.return_value = self.vehicle
        self.client = TestClient(self.app)

    def url(self, kind="photos", vehicle_id=1):
        return f"/api/vehicles/{vehicle_id}/attachments/archive/{kind}/"

    def test_member_downloads_separate_complete_archives_with_original_bytes(self):
        for scope, names, contents in [
            ("photos", ["صورة.png", "صورة (2).png"], self.contents[:2]),
            ("files", ["report.txt", "REPORT (2).txt"], self.contents[2:]),
        ]:
            with self.subTest(scope=scope):
                response = self.client.get(self.url(scope))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["content-type"], "application/zip")
                self.assertEqual(int(response.headers["content-length"]), len(response.content))
                self.assertIn("private, no-store", response.headers["cache-control"])
                self.assertIn(
                    f"HSPACE-050-001-{scope}.zip", response.headers["content-disposition"]
                )
                self.assertEqual(response.headers["x-content-type-options"], "nosniff")
                with ZipFile(io.BytesIO(response.content)) as archive:
                    self.assertEqual(archive.namelist(), names)
                    self.assertEqual([archive.read(name) for name in names], contents)
                    self.assertIsNone(archive.testzip())
                self.assertNotIn("storage_key", response.text)

    def test_download_requires_sign_in_and_only_the_two_scopes_exist(self):
        self.assertEqual(self.client.get(self.url("all")).status_code, 400)
        self.assertEqual(self.client.get(self.url("image")).status_code, 400)
        self.app.dependency_overrides.clear()
        for scope in ("photos", "files"):
            self.assertEqual(self.client.get(self.url(scope)).status_code, 401)

    def test_empty_deleted_or_wrong_vehicle_never_exports_an_attachment(self):
        self.repository.get_vehicle.return_value = replace(self.vehicle, attachments=())
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.repository.get_vehicle.return_value = self.vehicle
        self.assertEqual(self.client.get(self.url(vehicle_id=2)).status_code, 404)
        self.repository.get_vehicle.side_effect = NotFound("deleted parent")
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_missing_or_changed_file_fails_before_any_zip_is_sent(self):
        self.app.state.store.path(self.items[0].storage_key).unlink()
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"], "application/json")
        with self.app.state.store.path(self.items[0].storage_key).open("wb") as target:
            target.write(b"changed")
        self.assertEqual(self.client.get(self.url()).status_code, 503)

    def test_archive_names_are_flat_safe_and_case_insensitively_unique(self):
        names = ["../../CON.txt", r"C:\folder\CON.txt", "../..", "/صورة.png", "/صورة.png"]
        items = [
            replace(self.items[2], id=index, original_name=name)
            for index, name in enumerate(names, 1)
        ]
        with build_attachment_archive(items, self.app.state.store) as output, ZipFile(
            output
        ) as archive:
            self.assertEqual(
                archive.namelist(),
                ["_CON.txt", "_CON (2).txt", "attachment-3", "صورة.png", "صورة (2).png"],
            )
            for name in archive.namelist():
                self.assertNotIn("/", name)
                self.assertNotIn("\\", name)

    def test_temporary_archive_closes_after_download_or_response_failure(self):
        outputs = []

        def build(*args):
            output = build_attachment_archive(*args)
            outputs.append(output)
            return output

        with patch(
            "limousine.presentation.web.routes.vehicles.build_attachment_archive", side_effect=build
        ):
            self.assertEqual(self.client.get(self.url()).status_code, 200)
        self.assertTrue(outputs[0].closed)
        output = io.BytesIO(b"archive")
        response = ArchiveResponse(output, "private.zip")

        async def receive():
            return {"type": "http.disconnect"}

        async def fail_send(message):
            raise RuntimeError("client stopped")

        with self.assertRaisesRegex(RuntimeError, "client stopped"):
            asyncio.run(
                response(
                    {"type": "http", "method": "GET", "asgi": {"spec_version": "2.4"}},
                    receive,
                    fail_send,
                )
            )
        self.assertTrue(output.closed)

    def test_failed_archive_build_closes_temporary_storage(self):
        with patch(
            "limousine.infrastructure.attachment_archive.SpooledTemporaryFile",
            return_value=io.BytesIO(),
        ) as temporary:
            with self.assertRaises(OSError):
                build_attachment_archive([replace(self.items[0], size=1)], self.app.state.store)
            self.assertTrue(temporary.return_value.closed)
