"""Back up/upgrade the intended database, then roll back office-file fixtures."""

import io
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    import psycopg
    from fastapi.testclient import TestClient
    from PIL import Image

    from limousine.application.office import OfficeService
    from limousine.application.recycling import RecyclingService
    from limousine.config.runtime import load_settings
    from limousine.infrastructure.accounts import PostgresAccountRepository
    from limousine.infrastructure.attachments import LocalAttachmentStore
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.file_cleanup import FileCleanup
    from limousine.infrastructure.migrations import media_manifest, migrate
    from limousine.infrastructure.office import PostgresOfficeRepository
    from limousine.infrastructure.vehicle_repository import PostgresVehicleRepository
    from limousine.presentation.web.app import create_app
    from limousine.presentation.web.security import current_user

    settings = load_settings()
    assert (
        settings.db_host in ("localhost", "127.0.0.1", "::1")
        and settings.db_name == "limousine_local"
    )
    db = Database(settings)
    with db.connect() as conn:
        tables = [
            row["tablename"]
            for row in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename<>'hspace_schema_migration' ORDER BY tablename"
            )
        ]

    def snapshot():
        with db.connect() as conn:
            return {
                table: conn.execute("SELECT * FROM " + table + " ORDER BY 1").fetchall()
                for table in tables
            }

    before, files = snapshot(), media_manifest(settings.media_root)

    def preserved():
        assert snapshot() == before
        assert media_manifest(settings.media_root) == files

    migrate(db)
    preserved()
    assert migrate(db) is None
    operator = PostgresAccountRepository(db).operator()
    with TemporaryDirectory(prefix="hspace-office-") as directory, db.connect() as conn:

        class TransactionDatabase:
            @contextmanager
            def connect(self):
                yield conn

        transaction = TransactionDatabase()
        repo = PostgresOfficeRepository(transaction)
        service = OfficeService(repo)
        recycling = RecyclingService(PostgresVehicleRepository(transaction))
        store = LocalAttachmentStore(directory)
        cleanup = FileCleanup(transaction, store)
        app = create_app(settings)
        app.state.media_layout = None  # Fixture storage is managed by this script.
        app.state.office = service
        app.state.recycling = recycling
        app.state.store = store
        app.state.cleanup = cleanup
        app.dependency_overrides[current_user] = lambda: operator
        client = TestClient(app)
        client.get("/login/")
        headers = {"X-CSRFToken": client.cookies["csrftoken"]}
        base = "/api/office/attachments/"
        try:
            image = io.BytesIO()
            Image.new("RGB", (3, 2), "white").save(image, "PNG")
            image = image.getvalue()

            def upload(name, content):
                response = client.post(base, files={"file": (name, content)}, headers=headers)
                assert response.status_code == 201
                return response.json()["attachment"]

            photo = upload("office.png", image)
            doc = upload("office.txt", b"office original")
            assert client.get("/office/").status_code == 200
            assert client.get(photo["preview_url"]).content == image
            assert client.head(doc["download_url"]).status_code == 200
            for kind, item, content in [
                ("photos", photo, image),
                ("files", doc, b"office original"),
            ]:
                response = client.get(base + "archive/" + kind + "/")
                assert response.status_code == 200
                with ZipFile(io.BytesIO(response.content)) as zipped:
                    assert (
                        zipped.namelist() == [item["name"]] and zipped.read(item["name"]) == content
                    )
            response = client.patch(
                doc["manage_url"],
                json={"name": "Renamed", "expected_name": doc["name"]},
                headers=headers,
            )
            assert (
                response.status_code == 200
                and response.json()["attachment"]["name"] == "Renamed.txt"
            )
            assert (
                client.patch(
                    doc["manage_url"],
                    json={"name": "Stale", "expected_name": doc["name"]},
                    headers=headers,
                ).status_code
                == 409
            )
            item = service.get(doc["id"])
            assert store.path(item.storage_key).read_bytes() == b"office original"

            # Force an audit failure: metadata and event must form one transaction.
            def fail(*args):
                raise RuntimeError("Audit failure fixture")

            try:
                with conn.transaction(), patch.object(repo, "_event", side_effect=fail):
                    service.rename(doc["id"], "Rollback", "Renamed.txt", operator)
            except RuntimeError:
                pass
            else:
                raise AssertionError("Audit fixture did not fail.")
            assert service.get(doc["id"]).original_name == "Renamed.txt"
            assert client.delete(doc["manage_url"], headers=headers).status_code == 204
            assert client.get(doc["preview_url"]).status_code == 404
            assert client.get(base + "archive/files/").status_code == 404
            assert store.path(item.storage_key).is_file()
            cleanup.discard(item.storage_key)
            assert store.path(item.storage_key).is_file()
            deleted = client.get("/api/recycle-bin/").json()["items"]
            assert any(
                row["kind"] == "office"
                and row["id"] == doc["id"]
                and row["deleted_by"] == operator.username
                and row["vehicle_id"] is None
                for row in deleted
            )
            assert (
                client.post(
                    "/api/recycle-bin/office/" + str(doc["id"]) + "/restore/", headers=headers
                ).status_code
                == 204
            )
            assert client.get(doc["download_url"]).content == b"office original"
            events = [
                row
                for row in recycling.list_activity(operator)
                if row["entity_kind"] == "office" and row["entity_id"] == doc["id"]
            ]
            assert [row["action"] for row in events] == ["RESTORE", "DELETE", "RENAME", "CREATE"]
            assert all(row["vehicle_id"] is None for row in events)
            assert (
                events[0]["actor_name"] == operator.username
                and events[1]["actor_name"] == operator.username
            )
            for query, params in [
                ("DELETE FROM hspace_office_attachment WHERE id=%s", (doc["id"],)),
                ("UPDATE hspace_activity SET label=label WHERE id=%s", (events[0]["id"],)),
                (
                    "INSERT INTO hspace_activity(entity_kind,entity_id,action,actor_id,actor_name,label) VALUES ('vehicle',1,'CREATE',%s,'fixture','fixture')",
                    (operator.id,),
                ),
            ]:
                try:
                    with conn.transaction():
                        conn.execute(query, params)
                except psycopg.errors.CheckViolation:
                    pass
                else:
                    raise AssertionError("Retention/scope guard was bypassed.")
            rows = conn.execute(
                "SELECT storage_key FROM hspace_office_attachment WHERE id IN (%s,%s)",
                (photo["id"], doc["id"]),
            ).fetchall()
            assert all(row["storage_key"].startswith("office/") for row in rows)
            assert not conn.execute(
                "SELECT 1 FROM limo_attachment WHERE storage_key=ANY(%s)",
                ([row["storage_key"] for row in rows],),
            ).fetchone()
        finally:
            conn.rollback()
    preserved()
    print(
        "PASS: schema 8/idempotency, preserved existing rows/media; office upload, private originals, section ZIPs, rename/conflict, atomic audit rollback, operator deletion/operator recovery, retained bytes/cleanup, immutable events, scope guard and rolled-back fixtures. Sequences may advance."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        import traceback

        line = traceback.extract_tb(error.__traceback__)[-1].lineno
        print(
            f"FAIL: office verification ({type(error).__name__}, line {line}); private details suppressed.",
            file=sys.stderr,
        )
        raise SystemExit(1)
