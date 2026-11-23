"""Short PostgreSQL transactions, injected into persistence adapters."""

import psycopg
from psycopg.rows import dict_row


class Database:
    def __init__(
        self,
        settings,
    ):
        self.settings = settings

    def connect(self):
        if not self.settings.database_configured:
            raise psycopg.OperationalError("Database is not configured.")
        return psycopg.connect(
            dbname=self.settings.db_name,
            user=self.settings.db_user,
            password=self.settings.db_password,
            host=self.settings.db_host,
            port=self.settings.db_port,
            connect_timeout=5,
            row_factory=dict_row,
            options="-c statement_timeout=10000",
        )

    def ready(self):
        if not self.settings.database_configured:
            return "not_configured"
        try:
            with self.connect() as connection:
                connection.execute("SELECT 1").fetchone()
            return "ok"
        except psycopg.Error:
            return "unavailable"
