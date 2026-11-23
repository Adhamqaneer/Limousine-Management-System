"""Retryable private file removal after a metadata transaction commits."""

import logging

import psycopg

logger = logging.getLogger(__name__)


class FileCleanup:
    def __init__(
        self,
        database,
        store,
    ):
        self.database, self.store = database, store

    def discard(
        self,
        key,
    ):
        # An uncertain commit must never unlink a referenced (even deleted) file.
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO hspace_file_cleanup(storage_key) VALUES (%s) ON CONFLICT DO NOTHING",
                (key,),
            )
        return self.process(key)

    def process(
        self,
        key,
    ):
        try:
            with self.database.connect() as connection:
                row = connection.execute(
                    "SELECT storage_key FROM hspace_file_cleanup WHERE storage_key=%s FOR UPDATE",
                    (key,),
                ).fetchone()
                if not row:
                    return True
                # Preserve any still-referenced bytes, even if historical data shared a key.
                referenced = connection.execute(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM limo_attachment WHERE storage_key=%s
                        UNION ALL
                        SELECT 1 FROM limo_vehicle_cover WHERE storage_key=%s
                        UNION ALL
                        SELECT 1 FROM hspace_office_attachment WHERE storage_key=%s
                    ) AS used
                    """,
                    (key, key, key),
                ).fetchone()["used"]
                if not referenced:
                    self.store.delete(key)
                connection.execute(
                    "DELETE FROM hspace_file_cleanup WHERE storage_key=%s",
                    (key,),
                )
            return True
        except (OSError, psycopg.Error):
            # The durable queue entry survives both file errors and a failed commit.
            logger.warning("Private file cleanup deferred; retry the cleanup command.")
            return False

    def retry_pending(self):
        with self.database.connect() as connection:
            keys = connection.execute(
                "SELECT storage_key FROM hspace_file_cleanup ORDER BY created_at,storage_key LIMIT 100"
            ).fetchall()
        completed = sum(self.process(row["storage_key"]) for row in keys)
        return completed, len(keys) - completed
