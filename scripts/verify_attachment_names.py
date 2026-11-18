"""Back up/upgrade the intended local database; verify renames with rolled-back fixtures."""

import io
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from fastapi.testclient import TestClient
    from PIL import Image

    from limousine.application.vehicles import VehicleService
    from limousine.config.runtime import load_settings
    from limousine.domain.attachments import AttachmentNameConflict
    from limousine.infrastructure.accounts import PostgresAccountRepository
    from limousine.infrastructure.attachments import LocalAttachmentStore
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.migrations import media_manifest, migrate
    from limousine.infrastructure.vehicle_repository import PostgresVehicleRepository
    from limousine.presentation.web.app import create_app
    from limousine.presentation.web.security import current_user

    settings = load_settings()
    assert settings.db_name == "limousine_local" and settings.db_host in (
        "127.0.0.1",
        "localhost",
        "::1",
    )
    db = Database(settings)
    tables = (
        "limo_vehicle",
        "limo_attachment",
        "limo_vehicle_cover",
        "hspace_user",
        "hspace_session",
        "hspace_file_cleanup",
        "hspace_activity",
        "hspace_driver_assignment",
        "hspace_driver_change",
    )

    def snapshot():
        with db.connect() as conn:
            return {
                table: conn.execute("SELECT * FROM " + table + " ORDER BY 1").fetchall()
                for table in tables
            }

    before, files = snapshot(), media_manifest(settings.media_root)
    migrate(db)
    assert snapshot() == before and media_manifest(settings.media_root) == files
    assert migrate(db) is None
    with db.connect() as conn:
        assert conn.execute("SELECT 1 FROM hspace_schema_migration WHERE version=6").fetchone()
    member = next(
        user
        for user in PostgresAccountRepository(db).list_users()
        if user.role == "MEMBER" and user.can_login
    )
    with TemporaryDirectory(prefix="hspace-rename-") as directory, db.connect() as conn:

        class TransactionDatabase:
            @contextmanager
            def connect(self):
                yield conn

        repo = PostgresVehicleRepository(TransactionDatabase())
        service = VehicleService(repo)
        store = LocalAttachmentStore(directory)
        try:
            car = service.create_vehicle("00999-002", "Camry", actor=member)
            image = io.BytesIO()
            Image.new("RGB", (2, 2), "white").save(image, "PNG")
            items, contents = [], [image.getvalue(), b"original document 00123"]
            for name, content in zip(["Original.PNG", "Original.txt"], contents):
                source = io.BytesIO(content)
                stored = store.save(SimpleNamespace(name=name, size=len(content), read=source.read))
                items.append(service.add_attachment(car.id, actor=member, **vars(stored)))
            app = create_app(settings)
            app.state.media_layout = None  # Fixture storage is managed by this script.
            app.state.vehicles = service
            app.state.store = store
            app.dependency_overrides[current_user] = lambda: member
            client = TestClient(app)
            client.get("/login/")
            headers = {"X-CSRFToken": client.cookies["csrftoken"]}
            for item, stem, content in zip(items, ["صورة جديدة", "New document"], contents):
                url = f"/api/vehicles/{car.id}/attachments/{item.id}/"
                response = client.patch(
                    url, json={"name": stem, "expected_name": item.original_name}, headers=headers
                )
                assert response.status_code == 200
                updated = service.get_attachment(car.id, item.id)
                assert (updated.storage_key, updated.size, updated.created_at) == (
                    item.storage_key,
                    item.size,
                    item.created_at,
                )
                assert client.get(url + "download/").content == content
                assert (
                    client.patch(
                        url,
                        json={"name": stem, "expected_name": updated.original_name},
                        headers=headers,
                    ).status_code
                    == 200
                )
                assert (
                    client.patch(
                        url,
                        json={"name": "Stale", "expected_name": item.original_name},
                        headers=headers,
                    ).status_code
                    == 409
                )
                scope = "photos" if item.kind == "image" else "files"
                response = client.get(f"/api/vehicles/{car.id}/attachments/archive/{scope}/")
                assert response.status_code == 200
                with ZipFile(io.BytesIO(response.content)) as archive:
                    assert archive.namelist() == [updated.original_name]
                    assert archive.read(updated.original_name) == content
            events = [
                event
                for event in repo.list_activity()
                if event["vehicle_id"] == car.id and event["action"] == "RENAME"
            ]
            assert len(events) == 2 and all(
                event["actor_name"] == member.username for event in events
            )
            current = service.get_attachment(car.id, items[0].id)
            try:
                repo.rename_attachment(
                    car.id, current.id, "Stale.PNG", expected_name="old.PNG", actor=member
                )
            except AttachmentNameConflict:
                pass
            else:
                raise AssertionError("Missing locked-row conflict check.")
            try:
                with conn.transaction(), patch.object(
                    repo, "_event", side_effect=RuntimeError("fixture rollback")
                ):
                    service.rename_attachment(
                        car.id, current.id, "Not saved", current.original_name, actor=member
                    )
            except RuntimeError:
                pass
            else:
                raise AssertionError("Expected the audit write to fail.")
            assert service.get_attachment(car.id, current.id).original_name == current.original_name
            service.delete_attachment(car.id, current.id, actor=member)
            assert (
                client.patch(
                    f"/api/vehicles/{car.id}/attachments/{current.id}/",
                    json={"name": "Hidden", "expected_name": current.original_name},
                    headers=headers,
                ).status_code
                == 404
            )
            repo.delete_vehicle(car.id, member)
            assert (
                client.patch(
                    f"/api/vehicles/{car.id}/attachments/{items[1].id}/",
                    json={"name": "Hidden", "expected_name": "New document.txt"},
                    headers=headers,
                ).status_code
                == 404
            )
        finally:
            conn.rollback()
    assert snapshot() == before and media_manifest(settings.media_root) == files
    print(
        "PASS: schema 6/idempotency, original rows/files preserved, member rename/download/ZIP, fixed extensions, conflict checks, actor audit, transactional rollback and deleted-parent masking. Test fixtures rolled back; sequences may advance."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"FAIL: attachment-name verification ({type(error).__name__}); private details suppressed.",
            file=sys.stderr,
        )
        raise SystemExit(1)
