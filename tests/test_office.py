"""Office auth, original-file boundaries and use cases, without a runtime fallback."""

import io
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock
from zipfile import ZipFile

from fastapi.testclient import TestClient

from limousine.application.office import OfficeService
from limousine.config.runtime import Settings
from limousine.domain.accounts import AccessDenied
from limousine.domain.office import OfficeAttachment
from limousine.domain.vehicles import DomainError, NotFound
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import MEMBER
from tests.test_vehicle_http import STAMP, photo
from tests.uploads import SimpleUploadedFile


class OfficeTests(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.app = create_app(Settings(media_root=Path(temp.name)))
        self.app.dependency_overrides[current_user] = lambda: MEMBER
        self.repo = MagicMock()
        self.service = OfficeService(self.repo)
        self.app.state.office = self.service
        self.app.state.cleanup = MagicMock()
        self.image = photo()
        saved = self.app.state.store.save_office_file(SimpleUploadedFile("office.png", self.image))
        self.item = OfficeAttachment(
            7, saved.storage_key, "office.png", "image", len(self.image), STAMP
        )
        self.repo.get.return_value = self.item
        self.repo.list_files.return_value = [self.item]
        self.repo.add.return_value = self.item
        self.client = TestClient(self.app)
        self.client.get("/login/")
        self.headers = {"X-CSRFToken": self.client.cookies["csrftoken"]}
        self.base = "/api/office/attachments/"

    def test_member_page_list_originals_and_separate_zip(self):
        response = self.client.get("/office/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn("office-files.js", response.text)
        response = self.client.get(self.base)
        self.assertEqual(response.status_code, 200)
        item = response.json()["attachments"][0]
        self.assertNotIn("storage_key", item)
        self.assertEqual(item["manage_url"], self.base + "7/")
        for suffix in ("preview/", "download/"):
            response = self.client.get(self.base + "7/" + suffix)
            self.assertEqual(response.content, self.image)
            self.assertIn("no-store", response.headers["cache-control"])
            self.assertEqual(self.client.head(self.base + "7/" + suffix).status_code, 200)
        archive = self.client.get(self.base + "archive/photos/")
        with ZipFile(io.BytesIO(archive.content)) as zipped:
            self.assertEqual(zipped.read("office.png"), self.image)
        self.assertEqual(self.client.get(self.base + "archive/files/").status_code, 404)
        self.assertEqual(self.client.get(self.base + "archive/all/").status_code, 400)

    def test_upload_uses_office_namespace_and_cleans_failed_metadata(self):
        response = self.client.post(
            self.base, files={"file": ("office.txt", b"office bytes")}, headers=self.headers
        )
        self.assertEqual(response.status_code, 201)
        args = self.repo.add.call_args.args
        self.assertTrue(args[0].startswith("office/"))
        self.assertEqual(args[1:], ("office.txt", "file", 12, MEMBER))
        self.assertEqual(self.app.state.store.path(args[0]).read_bytes(), b"office bytes")
        self.repo.add.side_effect = DomainError("Failed metadata")
        self.assertEqual(
            self.client.post(
                self.base, files={"file": ("other.txt", b"bytes")}, headers=self.headers
            ).status_code,
            400,
        )
        self.assertTrue(self.app.state.cleanup.discard.call_args.args[0].startswith("office/"))
        self.assertEqual(
            self.client.post(
                self.base, files={"file": ("bad.exe", b"bytes")}, headers=self.headers
            ).status_code,
            400,
        )

    def test_member_rename_delete_csrf_and_stale_name(self):
        renamed = replace(self.item, original_name="New.png")
        self.repo.rename.return_value = renamed
        response = self.client.patch(
            self.base + "7/",
            json={"name": "New", "expected_name": "office.png"},
            headers=self.headers,
        )
        self.assertEqual(response.json()["attachment"]["name"], "New.png")
        self.repo.rename.assert_called_once_with(7, "New.png", "office.png", MEMBER)
        self.assertEqual(self.app.state.store.path(self.item.storage_key).read_bytes(), self.image)
        self.assertEqual(
            self.client.patch(
                self.base + "7/",
                json={"name": "New", "expected_name": "stale.png"},
                headers=self.headers,
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.patch(
                self.base + "7/",
                json={"name": "../bad", "expected_name": "office.png"},
                headers=self.headers,
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.delete(self.base + "7/", headers=self.headers).status_code, 204
        )
        self.repo.delete.assert_called_once_with(7, MEMBER)
        for method, kwargs in [
            ("delete", {}),
            ("patch", {"json": {"name": "A", "expected_name": "office.png"}}),
            ("post", {"files": {"file": ("a.txt", b"a")}}),
        ]:
            url = self.base if method == "post" else self.base + "7/"
            self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 403)

    def test_all_office_endpoints_require_authentication(self):
        self.app.dependency_overrides.clear()
        self.assertEqual(self.client.get("/office/", follow_redirects=False).status_code, 303)
        for path in ("", "7/preview/", "7/download/", "archive/photos/"):
            self.assertEqual(self.client.get(self.base + path).status_code, 401)
        self.assertEqual(
            self.client.post(
                self.base, files={"file": ("a.txt", b"a")}, headers=self.headers
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.patch(self.base + "7/", json={}, headers=self.headers).status_code, 401
        )
        self.assertEqual(
            self.client.delete(self.base + "7/", headers=self.headers).status_code, 401
        )

    def test_missing_deleted_files_and_domain_guards(self):
        self.repo.get.side_effect = NotFound("Deleted")
        self.assertEqual(self.client.get(self.base + "7/preview/").status_code, 404)
        for actor in (None, replace(MEMBER, is_active=False)):
            with self.assertRaises(AccessDenied):
                self.service.delete(7, actor)
        with self.assertRaises(DomainError):
            self.service.add("vehicles/key", "x", "file", 1, MEMBER)
        with self.assertRaises(DomainError):
            self.service.download("all")
