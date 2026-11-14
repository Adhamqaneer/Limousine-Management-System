import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from limousine.config.oracle import oracle_database


class OracleConfigurationTests(SimpleTestCase):
    def test_no_configuration_stays_oracle_and_is_not_ready(self):
        with patch.dict(os.environ, {}, clear=True):
            database, configured = oracle_database()
        self.assertFalse(configured)
        self.assertEqual(database["ENGINE"], "django.db.backends.oracle")

    def test_partial_configuration_fails_without_exposing_password(self):
        with patch.dict(os.environ, {"ORACLE_PASSWORD": "private-password"}, clear=True):
            with self.assertRaises(ImproperlyConfigured) as raised:
                oracle_database()
        self.assertIn("ORACLE_DSN", str(raised.exception))
        self.assertNotIn("private-password", str(raised.exception))

    def test_full_dsn_and_password_are_preserved(self):
        environment = {
            "ORACLE_DSN": "localhost:1521/freepdb1",
            "ORACLE_USER": "limousine",
            "ORACLE_PASSWORD": " significant-spaces ",
        }
        with patch.dict(os.environ, environment, clear=True):
            database, configured = oracle_database()
        self.assertTrue(configured)
        self.assertEqual(database["HOST"], "")
        self.assertEqual(database["PORT"], "")
        self.assertEqual(database["PASSWORD"], " significant-spaces ")

    def test_migrate_refuses_to_run_without_oracle_configuration(self):
        with self.assertRaisesMessage(CommandError, "Configure ORACLE_DSN"):
            call_command("migrate", verbosity=0)


class ProductionConfigurationTests(SimpleTestCase):
    def load_production_settings(self, overrides):
        environment = os.environ.copy()
        environment.update({
            "DJANGO_SETTINGS_MODULE": "limousine.config.settings.production",
            "DJANGO_SECRET_KEY": "x" * 64,
            "DJANGO_ALLOWED_HOSTS": "limousine.example",
            "ORACLE_DSN": "localhost:1521/freepdb1",
            "ORACLE_USER": "limousine",
            "ORACLE_PASSWORD": "not-used-for-a-connection",
            **overrides,
        })
        source = Path(__file__).resolve().parents[1] / "src"
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "from django.conf import settings; "
            "assert settings.DEBUG is False; "
            "print(settings.DATABASES['default']['ENGINE'])"
        )
        return subprocess.run(
            [sys.executable, "-c", code, str(source)],
            env=environment, capture_output=True, text=True, timeout=15,
        )

    def test_production_rejects_missing_secret(self):
        result = self.load_production_settings({"DJANGO_SECRET_KEY": ""})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_production_rejects_wildcard_hosts(self):
        result = self.load_production_settings({"DJANGO_ALLOWED_HOSTS": "*"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_production_rejects_missing_database(self):
        result = self.load_production_settings({"ORACLE_DSN": "", "ORACLE_USER": "", "ORACLE_PASSWORD": ""})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ORACLE_DSN", result.stderr)

    def test_production_configuration_keeps_oracle_and_debug_disabled(self):
        result = self.load_production_settings({})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("django.db.backends.oracle", result.stdout)
