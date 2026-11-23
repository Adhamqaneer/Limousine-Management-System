"""ZIP original bytes, safe per-vehicle names, scope validation and private HTTP."""

import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

from fastapi.testclient import TestClient

from limousine.application.attachment_download import (
    AttachmentDownloadService,
    VehicleArchiveSelection,
    selected_ids,
)
from limousine.config.runtime import Settings
from limousine.domain.accounts import AccessDenied
from limousine.domain.vehicles import DomainError, NotFound
from limousine.infrastructure.attachment_archive import build_vehicle_archive
from limousine.infrastructure.attachments import LocalAttachmentStore
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import OPERATOR


class AttachmentDownloadTests(TestCase):
    def test_availability_lists_every_vehicle_and_every_selected_type(self):
        repository = MagicMock()
        repository.availability.return_value = (
            [dict(id=10, plate_number="050-001"), dict(id=11, plate_number="050-002")],
            [dict(id=1, name="License"), dict(id=2, name="Card")],
            [dict(vehicle_id=10, category_id=1, count=2)],
        )
        service = AttachmentDownloadService(repository)
        result = service.availability([10, 11], [1, 2], OPERATOR)
        self.assertEqual(result["file_count"], 2)
        self.assertEqual(
            result["vehicles"][0]["documents"],
            [dict(category_id=1, count=2), dict(category_id=2, count=0)],
        )
        self.assertEqual(
            result["vehicles"][1]["documents"],
            [dict(category_id=1, count=0), dict(category_id=2, count=0)],
        )
        repository.availability.return_value = (
            [dict(id=11, plate_number="050-002")],
            [dict(id=1)],
            [],
        )
        self.assertEqual(
            service.availability([11], [1], OPERATOR)["vehicles"][0]["documents"][0]["count"], 0
        )

    def selection(self, directory):
        store = LocalAttachmentStore(directory)
        items = []
        for index, (vehicle, name, data) in enumerate(
            (
                (10, "license.pdf", b"%PDF-original"),
                (10, "LICENSE.pdf", b"another original"),
                (11, "../license.png", b"original image"),
            ),
            1,
        ):
            key = "vehicles/" + str(index) * 32 + ".pdf"
            path = store.path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            items.append(
                dict(
                    id=index,
                    vehicle_id=vehicle,
                    plate_number="050-001",
                    storage_key=key,
                    original_name=name,
                    size=len(data),
                    category_id=1,
                )
            )
        return store, VehicleArchiveSelection(
            tuple(items), ({"plate_number": "050-002", "category_name": "رخصة السيارة"},)
        )

    def test_zip_retains_all_formats_and_disambiguates_vehicle_and_file_names(self):
        with TemporaryDirectory() as directory:
            store, selection = self.selection(directory)
            with build_vehicle_archive(selection, store) as output, ZipFile(output) as archive:
                self.assertEqual(
                    archive.namelist(),
                    [
                        "050-001/license.pdf",
                        "050-001/LICENSE (2).pdf",
                        "050-001 (2)/license.png",
                        "_missing-documents.txt",
                    ],
                )
                self.assertEqual(archive.read("050-001/license.pdf"), b"%PDF-original")
                self.assertEqual(archive.read("050-001/LICENSE (2).pdf"), b"another original")
                self.assertEqual(archive.read("050-001 (2)/license.png"), b"original image")
                self.assertIn(
                    "050-002 : رخصة السيارة",
                    archive.read("_missing-documents.txt").decode("utf-8-sig"),
                )
                self.assertIsNone(archive.testzip())

    def test_missing_file_fails_before_response_and_closes_temporary_output(self):
        with TemporaryDirectory() as directory:
            store, selection = self.selection(directory)
            store.path(selection.files[0]["storage_key"]).unlink()
            output = io.BytesIO()
            with patch(
                "limousine.infrastructure.attachment_archive.SpooledTemporaryFile",
                return_value=output,
            ):
                with self.assertRaises(FileNotFoundError):
                    build_vehicle_archive(selection, store)
            self.assertTrue(output.closed)

    def test_selection_and_limits_keep_missing_types_explicit(self):
        repo = MagicMock()
        repo.selection.return_value = (
            [dict(id=10, plate_number="01"), dict(id=11, plate_number="02")],
            [dict(id=1, name="License")],
            [dict(vehicle_id=10, category_id=1, size=5)],
        )
        service = AttachmentDownloadService(repo)
        selection = service.select([10, 11], [1], OPERATOR)
        self.assertEqual(selection.missing, ({"plate_number": "02", "category_name": "License"},))
        with self.assertRaises(AccessDenied):
            service.select([10], [1], None)
        repo.selection.return_value = ([], [], [])
        with self.assertRaises(NotFound):
            service.select([10], [1], OPERATOR)
        repo.selection.return_value = ([], [], [dict(size=1024**3 + 1)])
        with self.assertRaises(DomainError):
            service.select([10], [1], OPERATOR)
        for invalid in ([], [True], [0], [2**63], "1"):
            with self.assertRaises(DomainError):
                selected_ids(invalid, 500)

    def test_authenticated_csrf_download_and_retired_print_routes(self):
        with TemporaryDirectory() as directory:
            app = create_app(Settings(media_root=Path(directory)))
            client = TestClient(app)
            self.assertEqual(client.post("/api/attachment-download/", json={}).status_code, 401)
            self.assertEqual(
                client.post("/api/attachment-download/availability/", json={}).status_code, 401
            )
            app.dependency_overrides[current_user] = lambda: OPERATOR
            app.state.attachment_download = MagicMock()
            store, selection = self.selection(directory)
            app.state.store = store
            app.state.attachment_download.select.return_value = selection
            client.get("/login/")
            body = {"vehicle_ids": [10, 11], "category_ids": [1]}
            self.assertEqual(client.post("/api/attachment-download/", json=body).status_code, 403)
            headers = {"X-CSRFToken": client.cookies["csrftoken"]}
            self.assertEqual(
                client.post("/api/attachment-download/availability/", json=body).status_code, 403
            )
            app.state.attachment_download.availability.return_value = {
                "vehicles": [],
                "file_count": 0,
            }
            checked = client.post(
                "/api/attachment-download/availability/", json=body, headers=headers
            )
            self.assertEqual(checked.status_code, 200)
            self.assertEqual(checked.json()["file_count"], 0)
            self.assertIn("no-store", checked.headers["cache-control"])
            response = client.post("/api/attachment-download/", json=body, headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"], "application/zip")
            self.assertIn("no-store", response.headers["cache-control"])
            self.assertEqual(response.headers["X-HSpace-File-Count"], "3")
            self.assertEqual(response.headers["X-HSpace-Missing-Count"], "1")
            with ZipFile(io.BytesIO(response.content)) as archive:
                self.assertEqual(archive.read("050-001/license.pdf"), b"%PDF-original")
            app.state.attachment_download.select.assert_called_once_with([10, 11], [1], OPERATOR)
            self.assertEqual(client.get("/reports/attachments/").status_code, 404)
            self.assertEqual(
                client.get("/api/vehicles/10/attachments/1/print-pages/1/").status_code, 404
            )
            self.assertEqual(client.get("/attachments/download/").status_code, 200)
