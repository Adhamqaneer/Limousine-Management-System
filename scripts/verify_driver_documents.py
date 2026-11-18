"""Upgrade the intended local database with backup; roll back driver/document fixtures."""

import io
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    import psycopg
    from fastapi.testclient import TestClient
    from PIL import Image

    from limousine.application.drivers import DriverService
    from limousine.application.recycling import RecyclingService
    from limousine.application.vehicles import VehicleService
    from limousine.config.runtime import load_settings
    from limousine.infrastructure.accounts import PostgresAccountRepository
    from limousine.infrastructure.attachments import LocalAttachmentStore
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.drivers import PostgresDriverRepository
    from limousine.infrastructure.file_cleanup import FileCleanup
    from limousine.infrastructure.migrations import media_manifest, migrate
    from limousine.infrastructure.vehicle_repository import PostgresVehicleRepository
    from limousine.presentation.web.app import create_app
    from limousine.presentation.web.security import administrator, current_user

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

    def preserved():
        after = snapshot()
        for table, rows in before.items():
            assert len(after[table]) == len(rows)
            for old, new in zip(rows, after[table]):
                assert all(new[key] == value for key, value in old.items())
                if table == "limo_attachment" and "driver_assignment_id" not in old:
                    assert new["driver_assignment_id"] is None
        assert media_manifest(settings.media_root) == files

    migrate(db)
    preserved()
    assert migrate(db) is None
    users = PostgresAccountRepository(db).list_users()
    member = next(user for user in users if user.role == "MEMBER" and user.can_login)
    admin = next(user for user in users if user.role == "ADMIN" and user.can_login)
    with TemporaryDirectory(prefix="hspace-driver-docs-") as directory, db.connect() as conn:

        class TransactionDatabase:
            @contextmanager
            def connect(self):
                yield conn

        transaction = TransactionDatabase()
        repo = PostgresVehicleRepository(transaction)
        vehicles = VehicleService(repo)
        drivers = DriverService(PostgresDriverRepository(transaction))
        store = LocalAttachmentStore(directory)
        app = create_app(settings)
        app.state.media_layout = None  # Fixture storage is managed by this script.
        app.state.vehicles = vehicles
        app.state.drivers = drivers
        app.state.store = store
        app.state.recycling = RecyclingService(repo)
        app.state.cleanup = FileCleanup(transaction, store)
        app.dependency_overrides[current_user] = lambda: member
        client = TestClient(app)
        client.get("/login/")
        headers = {"X-CSRFToken": client.cookies["csrftoken"]}
        try:
            car = vehicles.create_vehicle("00997-001", "Camry", actor=member)
            drivers.assign(car.id, "Old Driver", "00123", "2000-01-01", member)
            old = drivers.history(car.id)[0]
            image = io.BytesIO()
            Image.new("RGB", (2, 2), "white").save(image, "PNG")
            image = image.getvalue()
            base = f'/api/vehicles/{car.id}/drivers/{old["id"]}/attachments/'

            def upload(url, name, content):
                response = client.post(url, files={"file": (name, content)}, headers=headers)
                assert response.status_code == 201
                return response.json()["attachment"]

            photo = upload(base, "identity.png", image)
            document = upload(base, "licence.pdf", b"%PDF-1.7\n%%EOF")
            upload(f"/api/vehicles/{car.id}/attachments/", "vehicle.txt", b"vehicle only")
            assert drivers.history(car.id)[0]["attachment_count"] == 2
            assert len(vehicles.get_vehicle(car.id).attachments) == 1
            assert client.get(photo["preview_url"]).content == image
            assert (
                client.get(f'/api/vehicles/{car.id}/attachments/{photo["id"]}/preview/').status_code
                == 404
            )
            response = client.post(
                f'/api/vehicles/{car.id}/drivers/{old["id"]}/end/',
                json={"last_worked_on": "2000-01-10"},
                headers=headers,
            )
            assert (
                response.status_code == 200
                and response.json()["vehicle"]["driver_name"] == ""
                and response.json()["vehicle"]["driver_phone"] == ""
            )
            ended = drivers.history(car.id)[0]
            assert (
                ended["ended_on"].isoformat() == "2000-01-11"
                and ended["last_worked_on"].isoformat() == "2000-01-10"
            )
            assert drivers.history(car.id, on_date="2000-01-10") and not drivers.history(
                car.id, on_date="2000-01-11"
            )
            drivers.assign(car.id, "New Driver", "00456", "2000-01-20", member)
            current = drivers.history(car.id)[0]
            assert current["attachment_count"] == 0 and not drivers.history(
                car.id, on_date="2000-01-15"
            )
            assert vehicles.get_vehicle(car.id).driver_phone == "00456"
            assert (
                client.post(
                    f'/api/vehicles/{car.id}/drivers/{old["id"]}/end/',
                    json={"last_worked_on": "2000-01-25"},
                    headers=headers,
                ).status_code
                == 400
            )
            assert (
                client.post(
                    f'/api/vehicles/{car.id}/drivers/{current["id"]}/end/',
                    json={"last_worked_on": "2000-01-01"},
                    headers=headers,
                ).status_code
                == 400
            )
            drivers.assign(car.id, "Same Day Driver", "00789", "2000-01-20", member)
            same_day = next(row for row in drivers.history(car.id) if row["id"] == current["id"])
            assert (
                same_day["started_on"] == same_day["ended_on"]
                and same_day["last_worked_on"] is None
            )
            assert len(drivers.history(car.id, on_date="2000-01-20")) == 1
            assert len(client.get(base).json()["attachments"]) == 2
            upload(base, "historical.txt", b"historical period document")
            other = f'/api/vehicles/{car.id}/drivers/{current["id"]}/attachments/{photo["id"]}/'
            assert client.get(other + "download/").status_code == 404
            assert client.delete(other, headers=headers).status_code == 404
            renamed = client.patch(
                base + str(photo["id"]) + "/",
                json={"name": "هوية الشوفير", "expected_name": "identity.png"},
                headers=headers,
            )
            assert (
                renamed.status_code == 200
                and renamed.json()["attachment"]["name"] == "هوية الشوفير.png"
            )
            zipped = client.get(f"/api/vehicles/{car.id}/attachments/archive/files/")
            with ZipFile(io.BytesIO(zipped.content)) as archive:
                assert archive.namelist() == ["vehicle.txt"]
            assert (
                client.get(f"/api/vehicles/{car.id}/attachments/archive/photos/").status_code == 404
            )
            assert client.delete(base + str(photo["id"]) + "/", headers=headers).status_code == 204
            item = conn.execute(
                "SELECT * FROM limo_attachment WHERE id=%s", (photo["id"],)
            ).fetchone()
            assert (
                item["is_deleted"]
                and item["deleted_by"] == member.id
                and store.path(item["storage_key"]).read_bytes() == image
            )
            assert client.get(photo["download_url"]).status_code == 404
            assert any(
                row["id"] == photo["id"] and row["driver_name"] == "Old Driver"
                for row in repo.list_deleted()
            )
            app.dependency_overrides[administrator] = lambda: member
            assert (
                client.post(
                    f'/api/recycle-bin/attachment/{photo["id"]}/restore/', headers=headers
                ).status_code
                == 403
            )
            app.dependency_overrides[administrator] = lambda: admin
            assert (
                client.post(
                    f'/api/recycle-bin/attachment/{photo["id"]}/restore/', headers=headers
                ).status_code
                == 204
            )
            assert client.get(photo["download_url"]).content == image
            assert (
                conn.execute(
                    "SELECT driver_assignment_id FROM limo_attachment WHERE id=%s", (photo["id"],)
                ).fetchone()["driver_assignment_id"]
                == old["id"]
            )
            client.delete(base + str(photo["id"]) + "/", headers=headers)
            app.state.cleanup.discard(item["storage_key"])
            assert store.path(item["storage_key"]).is_file()
            repo.delete_vehicle(car.id, member)
            assert (
                client.get(base).status_code == 404
                and client.get(document["preview_url"]).status_code == 404
            )
            assert (
                client.post(
                    f"/api/recycle-bin/vehicle/{car.id}/restore/", headers=headers
                ).status_code
                == 204
            )
            assert (
                client.get(photo["download_url"]).status_code == 404
                and client.get(document["preview_url"]).status_code == 200
            )
            event = conn.execute(
                "SELECT * FROM hspace_driver_change WHERE vehicle_id=%s AND action='END'", (car.id,)
            ).fetchone()
            assert (
                event["actor_id"] == member.id
                and event["before_data"]["is_current"]
                and not event["after_data"]["is_current"]
            )
            assert event["after_data"]["ended_on"] == "2000-01-11"
            assert any(
                row["entity_id"] == photo["id"] and row["driver_name"] == "Old Driver"
                for row in repo.list_activity()
            )
            try:
                with conn.transaction():
                    conn.execute(
                        "UPDATE limo_vehicle SET driver_name='',driver_phone='' WHERE id=%s",
                        (car.id,),
                    )
            except psycopg.errors.CheckViolation:
                pass
            else:
                raise AssertionError("Current-driver guard was bypassed.")
            other_car = vehicles.create_vehicle(
                "00997-002", "Camry", driver_name="Legacy Driver", driver_phone="000", actor=member
            )
            legacy = drivers.history(other_car.id)[0]
            assert legacy["started_on"] is None
            drivers.end(other_car.id, legacy["id"], "2000-01-05", member)
            assert (
                vehicles.get_vehicle(other_car.id).driver_name == ""
                and drivers.history(other_car.id)[0]["started_on"] is None
            )
            try:
                with conn.transaction():
                    conn.execute(
                        "INSERT INTO limo_attachment(vehicle_id,driver_assignment_id,storage_key,original_name,kind,size,created_at) VALUES (%s,%s,%s,'mismatch.png','image',1,CURRENT_TIMESTAMP)",
                        (other_car.id, old["id"], "vehicles/" + uuid4().hex + ".png"),
                    )
            except psycopg.errors.ForeignKeyViolation:
                pass
            else:
                raise AssertionError("A driver attachment was linked to a different vehicle.")
        finally:
            conn.rollback()
    preserved()
    print(
        "PASS: schema 7/idempotency, preserved rows/media, inclusive ending/gaps/cache/audit, period-scoped upload/preview/download/rename, gallery and ZIP isolation, wrong-scope denial, member deletion/admin recovery, retained bytes, parent masking, FK/current guards and fixture rollback. Sequences may advance."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        import traceback

        line = traceback.extract_tb(error.__traceback__)[-1].lineno
        print(
            f"FAIL: driver-document verification ({type(error).__name__}, line {line}); private details suppressed.",
            file=sys.stderr,
        )
        raise SystemExit(1)
