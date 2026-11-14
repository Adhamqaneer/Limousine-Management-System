from unittest.mock import MagicMock, patch

from django.db import DatabaseError, InterfaceError
from django.test import SimpleTestCase, override_settings

from limousine.infrastructure.health import database_status


class HealthContractTests(SimpleTestCase):
    def test_home_is_english_and_does_not_need_a_database(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'lang="en" dir="ltr"')
        self.assertContains(response, "Limousine | Vehicles")
        self.assertContains(response, 'id="add-vehicle"')
        self.assertContains(response, 'id="detail-plate"')

    def test_liveness_does_not_probe_the_database(self):
        with patch("limousine.presentation.web.views.database_status") as probe:
            response = self.client.get("/health/live/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        probe.assert_not_called()

    def test_readiness_reports_unconfigured_database_and_is_not_cached(self):
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "not_ready", "database": "not_configured"})
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_readiness_is_successful_only_when_probe_succeeds(self):
        with patch("limousine.presentation.web.views.database_status", return_value="ok"):
            response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})

    def test_readiness_failure_is_not_reported_as_success(self):
        with patch("limousine.presentation.web.views.database_status", return_value="unavailable"):
            response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["database"], "unavailable")

    def test_health_endpoints_reject_mutations(self):
        for url in ("/health/live/", "/health/ready/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url).status_code, 405)

    def test_unknown_hosts_are_rejected(self):
        self.assertEqual(self.client.get("/", HTTP_HOST="untrusted.example").status_code, 400)


class OracleProbeTests(SimpleTestCase):
    @override_settings(ORACLE_CONFIGURED=False)
    def test_missing_configuration_does_not_open_a_connection(self):
        with patch("limousine.infrastructure.health.connections") as connections:
            self.assertEqual(database_status(), "not_configured")
        connections.__getitem__.assert_not_called()

    @override_settings(ORACLE_CONFIGURED=True)
    def test_connection_failure_is_redacted_and_connection_is_closed(self):
        connection = MagicMock()
        connection.cursor.side_effect = DatabaseError("private-host.example secret-password")
        with patch("limousine.infrastructure.health.connections", {"default": connection}):
            self.assertEqual(database_status(), "unavailable")
        connection.close.assert_called_once()

    @override_settings(ORACLE_CONFIGURED=True)
    def test_healthy_oracle_probe_closes_its_connection(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1,)
        with patch("limousine.infrastructure.health.connections", {"default": connection}):
            self.assertEqual(database_status(), "ok")
        connection.close.assert_called_once()

    @override_settings(ORACLE_CONFIGURED=True)
    def test_unexpected_probe_result_is_not_ready(self):
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = None
        with patch("limousine.infrastructure.health.connections", {"default": connection}):
            self.assertEqual(database_status(), "unavailable")

    @override_settings(ORACLE_CONFIGURED=True)
    def test_driver_interface_failure_is_not_an_http_server_error(self):
        connection = MagicMock()
        connection.cursor.side_effect = InterfaceError("disconnected")
        with patch("limousine.infrastructure.health.connections", {"default": connection}):
            self.assertEqual(database_status(), "unavailable")

    @override_settings(ORACLE_CONFIGURED=True)
    def test_connection_close_failure_is_not_reported_as_ready(self):
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)
        connection.close.side_effect = InterfaceError("connection close failed")
        with patch("limousine.infrastructure.health.connections", {"default": connection}):
            self.assertEqual(database_status(), "unavailable")
