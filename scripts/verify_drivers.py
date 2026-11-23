"""Upgrade intended local schema with backup, verify driver periods, roll back fixtures."""

import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def main():
    import psycopg
    from fastapi.testclient import TestClient

    from limousine.application.drivers import DriverService
    from limousine.application.recycling import RecyclingService
    from limousine.application.vehicles import VehicleService
    from limousine.config.runtime import load_settings
    from limousine.infrastructure.accounts import PostgresAccountRepository
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.drivers import PostgresDriverRepository
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
    )

    def snapshot():
        with db.connect() as conn:
            return {
                table: conn.execute("SELECT * FROM " + table + " ORDER BY 1").fetchall()
                for table in tables
            }

    before, files = snapshot(), media_manifest(settings.media_root)
    with db.connect() as conn:
        current = bool(
            conn.execute("SELECT 1 FROM hspace_schema_migration WHERE version=5").fetchone()
        )
    backup = migrate(db)
    assert snapshot() == before and media_manifest(settings.media_root) == files
    assert migrate(db) is None
    if not current:
        with db.connect() as conn:
            seeded = conn.execute("SELECT * FROM hspace_driver_assignment").fetchall()
            expected = [
                row for row in before["limo_vehicle"] if row["driver_name"] or row["driver_phone"]
            ]
            assert len(seeded) == len(expected)
            for row in seeded:
                old = next(item for item in expected if item["id"] == row["vehicle_id"])
                assert (row["driver_name"], row["driver_phone"]) == (
                    old["driver_name"],
                    old["driver_phone"],
                )
                assert (
                    row["started_on"] is None
                    and row["created_by"] is None
                    and row["created_at"] is None
                )
    operator = PostgresAccountRepository(db).operator()
    with db.connect() as conn:

        class TransactionDatabase:
            @contextmanager
            def connect(self):
                yield conn

        transactional = TransactionDatabase()
        repo = PostgresVehicleRepository(transactional)
        vehicles = VehicleService(repo)
        drivers = DriverService(PostgresDriverRepository(transactional))
        recycling = RecyclingService(repo)
        car = vehicles.create_vehicle(
            "00998-001", "Camry", driver_name="Old Driver", driver_phone="00123", actor=operator
        )
        initial = drivers.history(car.id)
        assert len(initial) == 1 and initial[0]["started_on"] is None
        app = create_app(settings)
        app.state.media_layout = None  # Fixture storage is managed by this script.
        app.state.drivers = drivers
        app.state.vehicles = vehicles
        app.dependency_overrides[current_user] = lambda: operator
        client = TestClient(app)
        client.get("/login/")
        headers = {"X-CSRFToken": client.cookies["csrftoken"]}

        def write(name, phone, start, correct=False):
            response = (client.patch if correct else client.post)(
                f"/api/vehicles/{car.id}/drivers/" + ("current/" if correct else ""),
                json={"driver_name": name, "driver_phone": phone, "started_on": start},
                headers=headers,
            )
            assert response.status_code == 200
            return response.json()["vehicle"]

        write("Old Driver", "00124", "2020-01-01", True)
        assert len(drivers.history(car.id)) == 1
        correction = drivers.corrections(car.id)[0]
        assert (
            correction["before_data"]["driver_phone"] == "00123"
            and correction["after_data"]["driver_phone"] == "00124"
        )
        assert correction["actor_name"] == operator.username
        write("New Driver", "0079", "2022-01-01")
        assert len(drivers.history(car.id)) == 2
        assert drivers.history(car.id, "", "2021-01-01")[0]["driver_name"] == "Old Driver"
        assert drivers.history(car.id, "", "2022-01-01")[0]["driver_name"] == "New Driver"
        assert vehicles.get_vehicle(car.id).driver_phone == "0079"
        assert len(drivers.history(car.id, "old")) == 1 and not drivers.history(car.id, "%")
        result = client.get(f"/api/drivers/?vehicle_id={car.id}&q=New&on_date=2022-01-01")
        assert result.status_code == 200 and len(result.json()["assignments"]) == 1
        invalid = {
            "driver_name": "Third Driver",
            "driver_phone": "0099",
            "started_on": "2021-01-01",
        }
        assert (
            client.post(
                f"/api/vehicles/{car.id}/drivers/", json=invalid, headers=headers
            ).status_code
            == 400
        )
        assert len(drivers.history(car.id)) == 2
        assert (
            client.patch(
                f"/api/vehicles/{car.id}/", json={"driver_phone": "123"}, headers=headers
            ).status_code
            == 400
        )
        write("Old Driver", "0009", "2023-01-01")
        assert len(drivers.history(car.id, "Old")) == 2
        assert len(drivers.history(car.id)) == 3
        try:
            with conn.transaction():
                conn.execute(
                    "UPDATE limo_vehicle SET driver_phone=%s WHERE id=%s", ("wrong", car.id)
                )
        except psycopg.errors.CheckViolation:
            pass
        else:
            raise AssertionError("Direct driver overwrite allowed")
        recycling.delete_vehicle(car.id, operator)
        assert client.get("/api/drivers/?q=Old").status_code == 200
        assert not any(row["vehicle_id"] == car.id for row in drivers.history())
        assert client.get(f"/api/vehicles/{car.id}/drivers/").status_code == 404
        assert (
            conn.execute(
                "SELECT count(*) AS n FROM hspace_driver_assignment WHERE vehicle_id=%s", (car.id,)
            ).fetchone()["n"]
            == 3
        )
        conn.rollback()
    assert snapshot() == before and media_manifest(settings.media_root) == files
    print(
        "PASS: schema 5/idempotency, preserved existing values/files, unknown historical starts, assignment/correction audit, day boundaries, phone snapshots, name/date search, parent masking, overwrite guard and fixture rollback."
    )
    print("Private pre-upgrade backup created." if backup else "Schema already current.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Driver verification failed ({type(error).__name__}); private details suppressed.")
        raise SystemExit(1)
