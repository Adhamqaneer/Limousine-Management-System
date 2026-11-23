from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from limousine.config.runtime import Settings
from limousine.presentation.web.factory import create_app


class DesktopSetupTests(TestCase):
    def test_website_has_no_first_run_route(self):
        with TestClient(create_app(Settings())) as client:
            self.assertEqual(client.get("/desktop/setup/?token=test").status_code, 404)

    @patch("limousine.presentation.web.routes.desktop_setup.migrate")
    @patch("limousine.presentation.web.routes.desktop_setup.needs_operator_setup")
    def test_setup_requires_one_time_launcher_token_and_csrf(self, needs_setup, migrate):
        token = "desktop-test-token"
        app = create_app(Settings(), setup_token=token)
        needs_setup.return_value = True
        with TestClient(app) as client:
            self.assertEqual(client.get("/desktop/setup/").status_code, 404)
            response = client.get("/desktop/setup/", params={"token": token})
            self.assertIn("Set your password", response.text)
            self.assertIn('autocomplete="new-password"', response.text)
            self.assertNotIn(token, str(response.url))
            self.assertEqual(client.get("/desktop/setup/", params={"token": token}).status_code, 404)

            password = "Test-passphrase"
            data = {
                "password": password,
                "confirmation": password,
            }
            self.assertEqual(client.post("/desktop/setup/", data=data).status_code, 403)
            data["csrfmiddlewaretoken"] = client.cookies["csrftoken"]
            self.assertEqual(
                client.post("/desktop/setup/", data={**data, "confirmation": "different"}).status_code,
                400,
            )
            migrate.assert_not_called()

            response = client.post("/desktop/setup/", data=data, follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/login/")
            migrate.assert_called_once_with(app.state.database, operator_password=password)

            needs_setup.return_value = False
            self.assertEqual(client.get("/desktop/setup/", params={"token": token}).status_code, 404)
            self.assertEqual(client.get("/desktop/setup/").status_code, 404)
            self.assertEqual(client.post("/desktop/setup/", data=data).status_code, 404)
