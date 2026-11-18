"""Templates must request changed assets rather than stale per-page translations."""

import re
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from limousine.config.runtime import Settings
from limousine.presentation.web import rendering
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import MEMBER


class StaticAssetTests(TestCase):
    def test_generated_daylight_webp_has_image_content_type(self):
        client = TestClient(create_app(Settings()))
        response = client.get("/static/web/hspace-camry-daylight.webp")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/webp")
        self.assertTrue(response.content.startswith(b"RIFF"))

    def test_asset_version_stable_until_content_changes(self):
        with TemporaryDirectory() as directory, patch.object(
            rendering, "STATIC_ROOT", Path(directory)
        ):
            file = Path(directory) / "script.js"
            file.write_text("first", encoding="utf-8")
            old = rendering.static_url("script.js")
            self.assertEqual(rendering.static_url("script.js"), old)
            file.write_text("new translation", encoding="utf-8")
            self.assertNotEqual(rendering.static_url("script.js"), old)
            self.assertTrue(old.startswith("/static/script.js?v="))

    def test_vehicle_and_report_pages_deliver_versioned_translations(self):
        app = create_app(Settings())
        app.dependency_overrides[current_user] = lambda: MEMBER
        client = TestClient(app)
        for page, script in [("/", "app.js"), ("/reports/vehicles/", "vehicle-report.js")]:
            html = client.get(page).text
            match = re.search(
                r'src="(/static/web/' + re.escape(script) + r'\?v=[0-9a-f]{16})"', html
            )
            self.assertIsNotNone(match)
            response = client.get(match.group(1))
            self.assertEqual(response.status_code, 200)
            self.assertRegex(response.text, r"navOffice:\s*['\"]ملفات المكتب['\"]")
            self.assertIn("no-store", client.get(page).headers["cache-control"])
