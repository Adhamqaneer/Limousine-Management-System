from unittest import TestCase

from limousine.config.runtime import Settings


class ConfigurationTests(TestCase):
    def test_partial_postgres_configuration_is_rejected_without_secret(self):
        with self.assertRaises(ValueError) as result:
            Settings(db_password="private-value").validate()
        self.assertNotIn("private-value", str(result.exception))

    def test_unconfigured_state_does_not_select_another_database(self):
        self.assertFalse(Settings().validate().database_configured)

    def test_production_requires_explicit_secure_settings(self):
        with self.assertRaises(ValueError):
            Settings(production=True).validate()
        with self.assertRaises(ValueError):
            Settings(
                db_name="db",
                db_user="app",
                db_password="private",
                secret="x" * 64,
                production=True,
                allowed_hosts=("*",),
            ).validate()
        self.assertTrue(
            Settings(
                db_name="db",
                db_user="app",
                db_password="private",
                secret="x" * 64,
                production=True,
                allowed_hosts=("office.example",),
            )
            .validate()
            .production
        )
