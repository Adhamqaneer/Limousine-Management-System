from unittest import TestCase
from unittest.mock import patch
from fastapi.testclient import TestClient
from limousine.config.runtime import Settings
from limousine.presentation.web.app import create_app

class HealthTests(TestCase):
    def setUp(self):
        self.app=create_app(Settings())
        self.client=TestClient(self.app)

    def test_login_is_branded_and_does_not_require_database(self):
        response=self.client.get("/login/")
        self.assertEqual(response.status_code,200)
        self.assertIn("H SPACE | Sign in",response.text)
        self.assertIn('autocomplete="current-password"',response.text)
        self.assertIn('lang="en" dir="ltr"',response.text)
        self.assertIn("no-store",response.headers["cache-control"])

    def test_liveness_never_queries_database(self):
        with patch.object(self.app.state.database,"connect") as connect:
            self.assertEqual(self.client.get("/health/live/").json(),{"status":"ok"})
        connect.assert_not_called()

    def test_readiness_reports_missing_or_failed_storage(self):
        self.assertEqual(self.client.get("/health/ready/").status_code,503)
        with patch.object(self.app.state.database,"ready",return_value="ok"):
            self.assertEqual(self.client.get("/health/ready/").status_code,200)

    def test_unknown_hosts_and_unsafe_health_methods_are_rejected(self):
        self.assertEqual(self.client.get("/login/",headers={"host":"untrusted.example"}).status_code,400)
        self.assertEqual(self.client.post("/health/live/").status_code,405)
