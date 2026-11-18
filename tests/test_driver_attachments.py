from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from limousine.application.vehicles import VehicleService
from limousine.config.runtime import Settings
from limousine.domain.vehicles import Attachment, NotFound, Vehicle
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import MEMBER
from tests.test_vehicle_http import STAMP, photo
from tests.uploads import SimpleUploadedFile


class DriverAttachmentTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.app = create_app(Settings(media_root=Path(directory.name)))
        self.app.dependency_overrides[current_user] = lambda: MEMBER
        self.service = MagicMock()
        self.app.state.vehicles = self.service
        self.service.get_vehicle.return_value = Vehicle(1, "001", STAMP, vehicle_type="Camry")
        content = photo()
        saved = self.app.state.store.save(SimpleUploadedFile("identity.png", content))
        self.item = Attachment(
            5, 1, saved.storage_key, "identity.png", "image", len(content), STAMP, 4
        )
        self.service.driver_attachments.return_value = [self.item]
        self.service.add_attachment.return_value = self.item
        self.service.get_attachment.return_value = self.item
        self.service.rename_attachment.return_value = replace(self.item, original_name="New.png")
        self.app.state.cleanup = MagicMock()
        self.client = TestClient(self.app)
        self.client.get("/login/")
        self.headers = {"X-CSRFToken": self.client.cookies["csrftoken"]}
        self.base = "/api/vehicles/1/drivers/4/attachments/"

    def test_member_lists_uploads_previews_downloads_renames_and_deletes_in_scope(self):
        response = self.client.get(self.base)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["attachments"][0]["preview_url"], self.base + "5/preview/")
        self.assertIn("private, no-store", response.headers["cache-control"])
        self.assertEqual(self.client.get(self.base + "5/preview/").content, photo())
        self.assertEqual(self.client.get(self.base + "5/download/").content, photo())
        self.service.get_attachment.assert_called_with(1, 5, assignment_id=4)
        self.assertEqual(
            self.client.post(
                self.base,
                files={"file": ("identity.png", photo(), "image/png")},
                headers=self.headers,
            ).status_code,
            201,
        )
        self.assertEqual(self.service.add_attachment.call_args.kwargs["assignment_id"], 4)
        self.assertEqual(self.service.add_attachment.call_args.kwargs["actor"], MEMBER)
        body = {"name": "New", "expected_name": "identity.png"}
        self.assertEqual(
            self.client.patch(self.base + "5/", json=body, headers=self.headers).status_code, 200
        )
        self.service.rename_attachment.assert_called_once_with(
            1, 5, "New", "identity.png", actor=MEMBER, assignment_id=4
        )
        self.assertEqual(
            self.client.delete(self.base + "5/", headers=self.headers).status_code, 204
        )
        self.service.delete_attachment.assert_called_once_with(1, 5, actor=MEMBER, assignment_id=4)

    def test_mutations_require_csrf_and_all_routes_require_authentication(self):
        self.assertEqual(
            self.client.post(self.base, files={"file": ("identity.png", photo())}).status_code, 403
        )
        self.assertEqual(self.client.delete(self.base + "5/").status_code, 403)
        self.assertEqual(
            self.client.patch(
                self.base + "5/", json={"name": "New", "expected_name": "identity.png"}
            ).status_code,
            403,
        )
        self.app.dependency_overrides.clear()
        for suffix in ("", "5/preview/", "5/download/"):
            self.assertEqual(self.client.get(self.base + suffix).status_code, 401)

    def test_invalid_period_upload_is_rejected_before_storing_bytes(self):
        before = set(Path(self.app.state.settings.media_root).rglob("*"))
        self.service.driver_attachments.side_effect = NotFound("Wrong period or deleted parent")
        self.assertEqual(
            self.client.post(
                self.base, files={"file": ("identity.png", photo())}, headers=self.headers
            ).status_code,
            404,
        )
        self.assertEqual(set(Path(self.app.state.settings.media_root).rglob("*")), before)

    def test_attachment_context_cannot_be_bypassed_by_vehicle_or_other_period(self):
        from limousine.domain.accounts import AccessDenied

        repo = MagicMock()
        repo.get_attachment.return_value = self.item
        service = VehicleService(repo)
        for assignment in (None, 99):
            with self.assertRaises(NotFound):
                service.get_attachment(1, 5, assignment_id=assignment)
        self.assertEqual(service.get_attachment(1, 5, assignment_id=4), self.item)
        with self.assertRaises(AccessDenied):
            service.add_attachment(
                1,
                storage_key="key",
                original_name="identity.png",
                kind="image",
                size=10,
                assignment_id=4,
            )
