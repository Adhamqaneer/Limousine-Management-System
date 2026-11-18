"""Organize originals without deleting their only copy before metadata commits."""

import hashlib
import logging
import shutil
from contextlib import contextmanager
from pathlib import PurePosixPath

import psycopg

from limousine.domain.vehicles import NotFound
from limousine.infrastructure.file_cleanup import FileCleanup
from limousine.infrastructure.media_paths import driver_directory, section_for, vehicle_directory

logger = logging.getLogger(__name__)
MEDIA_LOCK_ID = 72730805


class MediaOrganizer:
    def __init__(self, database, store):
        self.database = database
        self.store = store
        self.cleanup = FileCleanup(database, store)
        self._copied_keys = []

    @contextmanager
    def operation(self):
        # Serialize uploads/date changes even when multiple web processes are running.
        with self.database.connect() as lock_connection:
            lock_connection.execute("SELECT pg_advisory_lock(%s)", (MEDIA_LOCK_ID,))
            self._copied_keys = []
            try:
                yield
            except Exception:
                # Even an uncertain commit is safe: cleanup checks all references.
                for key in self._copied_keys:
                    try:
                        self.cleanup.discard(key)
                    except (OSError, psycopg.Error):
                        logger.warning("An unsuccessful media copy remains for cleanup.")
                raise
            else:
                # The caller's metadata transaction has committed before cleanup.
                try:
                    while True:
                        completed, deferred = self.cleanup.retry_pending()
                        if deferred or completed < 100:
                            break
                except (OSError, psycopg.Error):
                    logger.warning("Old media copies remain queued for cleanup.")
            finally:
                lock_connection.execute("SELECT pg_advisory_unlock(%s)", (MEDIA_LOCK_ID,))

    def ensure_directory(self, directory):
        marker = self.store.path(directory + "/" + "0" * 32 + ".txt")
        marker.parent.mkdir(parents=True, exist_ok=True)

    def ensure_sections(self, directory, *, covers=False):
        for section in ("photos", "files"):
            self.ensure_directory(directory + "/" + section)
        if covers:
            self.ensure_directory(directory + "/covers")

    def upload_directory(self, vehicle_id, assignment_id=None, *, cover=False):
        if assignment_id is None:
            directory = vehicle_directory(vehicle_id)
            self.ensure_sections(directory, covers=True)
            return directory
        with self.database.connect() as connection:
            assignment = connection.execute(
                "SELECT * FROM hspace_driver_assignment WHERE id=%s AND vehicle_id=%s",
                (assignment_id, vehicle_id),
            ).fetchone()
            if not assignment:
                raise NotFound("Driver period not found.")
            directory = driver_directory(assignment)
            self.ensure_sections(directory)
            return directory

    @staticmethod
    def digest(path):
        with path.open("rb") as source:
            return hashlib.file_digest(source, "sha256").digest()

    def relocate(self, connection, table, row, directory):
        old_key = row["storage_key"]
        new_key = directory + "/" + PurePosixPath(old_key).name
        if old_key == new_key:
            return
        source = self.store.path(old_key)
        target = self.store.path(new_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if self.digest(source) != self.digest(target):
                raise OSError("A different file already occupies the organized path.")
        else:
            created = False
            try:
                with source.open("rb") as original, target.open("xb") as destination:
                    created = True
                    shutil.copyfileobj(original, destination, 65536)
                if target.stat().st_size != row["size"] or self.digest(source) != self.digest(
                    target
                ):
                    raise OSError("The copied original is incomplete.")
            except Exception:
                if created:
                    target.unlink(missing_ok=True)
                raise
        self._copied_keys.append(new_key)
        # Table names are internal constants; storage keys remain parameters.
        from psycopg import sql

        connection.execute(
            sql.SQL("UPDATE {} SET storage_key=%s WHERE id=%s").format(sql.Identifier(table)),
            (new_key, row["id"]),
        )
        connection.execute(
            "INSERT INTO hspace_file_cleanup(storage_key) VALUES (%s) ON CONFLICT DO NOTHING",
            (old_key,),
        )

    def organize_driver(self, connection, assignment_id):
        assignment = connection.execute(
            "SELECT * FROM hspace_driver_assignment WHERE id=%s", (assignment_id,)
        ).fetchone()
        if not assignment:
            raise NotFound("Driver period not found.")
        directory = driver_directory(assignment)
        self.ensure_sections(directory)
        driver_root = self.store.root.resolve() / "drivers"
        current_folder = self.store.path(directory + "/photos/" + "0" * 32 + ".txt").parent.parent
        for previous in driver_root.glob(f"*--period-{assignment_id}"):
            if previous == current_folder or previous.is_symlink():
                continue
            if not previous.resolve().is_relative_to(driver_root):
                continue
            for section in ("photos", "files"):
                try:
                    (previous / section).rmdir()
                except OSError:
                    pass
            try:
                previous.rmdir()
            except OSError:
                pass
        rows = connection.execute(
            "SELECT * FROM limo_attachment WHERE driver_assignment_id=%s ORDER BY id FOR UPDATE",
            (assignment_id,),
        ).fetchall()
        for row in rows:
            self.relocate(
                connection, "limo_attachment", row, directory + "/" + section_for(row["kind"])
            )

    def organize_all(self):
        with self.operation():
            with self.database.connect() as connection:
                connection.execute(
                    "LOCK TABLE limo_vehicle, hspace_driver_assignment, limo_attachment, "
                    "limo_vehicle_cover, hspace_office_attachment IN SHARE ROW EXCLUSIVE MODE"
                )
                self.ensure_sections("office")
                for row in connection.execute(
                    "SELECT * FROM hspace_office_attachment ORDER BY id"
                ).fetchall():
                    self.relocate(
                        connection,
                        "hspace_office_attachment",
                        row,
                        "office/" + section_for(row["kind"]),
                    )
                for vehicle in connection.execute(
                    "SELECT id FROM limo_vehicle ORDER BY id"
                ).fetchall():
                    self.ensure_sections(vehicle_directory(vehicle["id"]), covers=True)
                for row in connection.execute(
                    "SELECT * FROM limo_attachment WHERE driver_assignment_id IS NULL ORDER BY id"
                ).fetchall():
                    self.relocate(
                        connection,
                        "limo_attachment",
                        row,
                        vehicle_directory(row["vehicle_id"]) + "/" + section_for(row["kind"]),
                    )
                for row in connection.execute(
                    "SELECT * FROM limo_vehicle_cover ORDER BY id"
                ).fetchall():
                    self.relocate(
                        connection,
                        "limo_vehicle_cover",
                        row,
                        vehicle_directory(row["vehicle_id"]) + "/covers",
                    )
                for row in connection.execute(
                    "SELECT id FROM hspace_driver_assignment ORDER BY id"
                ).fetchall():
                    self.organize_driver(connection, row["id"])
