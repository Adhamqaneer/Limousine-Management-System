"""Verify categories/downloads on local PostgreSQL with rolled-back, private fixtures."""

import io
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from fastapi.testclient import TestClient
    from PIL import Image
    from psycopg.errors import UniqueViolation

    from limousine.application.attachment_download import AttachmentDownloadService
    from limousine.application.categories import CategoryService
    from limousine.application.drivers import DriverService
    from limousine.application.office import OfficeService
    from limousine.application.recycling import RecyclingService
    from limousine.application.vehicles import VehicleService
    from limousine.config.runtime import load_settings
    from limousine.infrastructure.accounts import PostgresAccountRepository
    from limousine.infrastructure.attachment_download import (
        PostgresAttachmentDownloadRepository,
    )
    from limousine.infrastructure.attachments import LocalAttachmentStore
    from limousine.infrastructure.categories import PostgresCategoryRepository
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.drivers import PostgresDriverRepository
    from limousine.infrastructure.migrations import media_manifest, migrate
    from limousine.infrastructure.office import PostgresOfficeRepository
    from limousine.infrastructure.vehicle_repository import PostgresVehicleRepository
    from limousine.presentation.web.app import create_app
    from limousine.presentation.web.security import current_user

    settings = load_settings()
    assert settings.db_name == "limousine_local" and settings.db_host in (
        "localhost",
        "127.0.0.1",
        "::1",
    )
    database = Database(settings)
    assert migrate(database) is None, "Apply the documented migration first."
    originals = media_manifest(settings.media_root)
    operator = PostgresAccountRepository(database).operator()
    tables = (
        "limo_vehicle",
        "limo_attachment",
        "hspace_office_attachment",
        "hspace_attachment_category",
        "hspace_category_alias",
        "hspace_activity",
        "hspace_driver_assignment",
    )

    def snapshot():
        with database.connect() as connection:
            return {
                table: connection.execute("SELECT * FROM " + table + " ORDER BY 1").fetchall()
                for table in tables
            }

    original_records = snapshot()
    with database.connect() as connection, TemporaryDirectory(
        prefix="hspace-category-"
    ) as directory:

        class FixtureConnection:
            def execute(self, query, *args):
                # The outer read/write fixture transaction provides the snapshot.
                # Production selection still uses its own read-only transaction.
                if isinstance(query, str) and query.startswith("SET TRANSACTION"):
                    return None
                return connection.execute(query, *args)

        class FixtureDatabase:
            @contextmanager
            def connect(self):
                yield FixtureConnection()

        fixture_db = FixtureDatabase()
        category_repo = PostgresCategoryRepository(fixture_db)
        app = create_app(settings)
        app.state.media_layout = None
        app.state.store = LocalAttachmentStore(directory)
        app.state.categories = CategoryService(category_repo)
        app.state.vehicles = VehicleService(PostgresVehicleRepository(fixture_db))
        app.state.recycling = RecyclingService(PostgresVehicleRepository(fixture_db))
        app.state.office = OfficeService(PostgresOfficeRepository(fixture_db))
        app.state.drivers = DriverService(PostgresDriverRepository(fixture_db))
        app.state.attachment_download = AttachmentDownloadService(
            PostgresAttachmentDownloadRepository(fixture_db)
        )
        app.dependency_overrides[current_user] = lambda: operator
        client = TestClient(app)
        client.get("/login/")
        headers = {"X-CSRFToken": client.cookies["csrftoken"]}

        def post(url, payload, status=200):
            response = client.post(url, json=payload, headers=headers)
            assert response.status_code == status, (url, response.status_code)
            return response.json()

        def upload(url, name, content, category_id=None):
            response = client.post(
                url,
                files={"file": (name, content)},
                data={"category_id": str(category_id)} if category_id is not None else None,
                headers=headers,
            )
            assert response.status_code == 201, response.status_code
            return response.json()["attachment"]

        try:
            initial = client.get("/api/attachment-categories/").json()["categories"]
            assert initial[-1]["is_other"]
            other = initial[-1]["id"]
            source = post("/api/attachment-categories/", {"name": "Fixture Insurance"})["category"][
                "id"
            ]
            exact = post("/api/attachment-categories/", {"name": " fixture-insurance "})[
                "category"
            ]["id"]
            assert exact == source
            post("/api/attachment-categories/", {"name": "Fixture Insurance extra"}, 409)
            target = post(
                "/api/attachment-categories/",
                {"name": "Fixture Insurance extra", "allow_similar": True},
            )["category"]["id"]
            post(f"/api/attachment-categories/{source}/aliases/", {"name": "Fixture policy"})
            assert (
                post("/api/attachment-categories/", {"name": "FIXTURE POLICY"})["category"]["id"]
                == source
            )
            post(f"/api/attachment-categories/{target}/aliases/", {"name": "Fixture policy"}, 409)
            post(f"/api/attachment-categories/{source}/merge/", {"target_id": other}, 400)
            car = app.state.vehicles.create_vehicle(
                "00999-901", "Camry", actor=operator, driver_name="Fixture Driver"
            )
            missing_car = app.state.vehicles.create_vehicle("00999-902", "Camry", actor=operator)
            base = f"/api/vehicles/{car.id}/attachments/"
            image = io.BytesIO()
            Image.new("RGB", (10, 8), "white").save(image, "PNG")
            image_bytes = image.getvalue()
            deleted = upload(base, "Deleted.txt", b"retained deleted bytes", source)
            assert client.delete(deleted["manage_url"], headers=headers).status_code == 204
            picture = upload(base, "Picture.png", image_bytes, source)
            pdf_bytes = b"%PDF-1.7\nfixture original PDF\n%%EOF"
            pdf = upload(base, "Document.pdf", pdf_bytes, other)
            upload(base, "Notes.txt", b"original notes", other)
            office = upload("/api/office/attachments/", "Office.txt", b"office original")
            assert "category_id" not in office
            assert connection.execute(
                "SELECT category_id FROM hspace_office_attachment WHERE id=%s", (office["id"],)
            ).fetchone()["category_id"] == other
            # Simulate an office attachment classified before that feature was removed.
            connection.execute(
                "UPDATE hspace_office_attachment SET category_id=%s WHERE id=%s",
                (source, office["id"]),
            )
            period = connection.execute(
                "SELECT id FROM hspace_driver_assignment WHERE vehicle_id=%s AND is_current",
                (car.id,),
            ).fetchone()["id"]
            driver = upload(
                f"/api/vehicles/{car.id}/drivers/{period}/attachments/",
                "Driver.png",
                image_bytes,
                source,
            )
            post(f"/api/attachment-categories/{source}/merge/", {"target_id": target})
            assert app.state.categories.get(source)["id"] == target
            assert connection.execute(
                "SELECT count(*) AS n FROM limo_attachment WHERE category_id=%s", (source,)
            ).fetchone()["n"] == 0
            assert connection.execute(
                "SELECT category_id FROM hspace_office_attachment WHERE id=%s", (office["id"],)
            ).fetchone()["category_id"] == source
            assert connection.execute(
                "SELECT category_id,is_deleted FROM limo_attachment WHERE id=%s", (deleted["id"],)
            ).fetchone() == dict(category_id=target, is_deleted=True)
            # A stale upload picker resolves the merged source while holding the merge lock.
            rejected = client.post(
                base,
                files={"file": ("Duplicate.txt", b"duplicate")},
                data={"category_id": str(source)},
                headers=headers,
            )
            assert (
                rejected.status_code == 409
                and rejected.json()["error"]["code"] == "category_in_use"
            )
            stale = upload(base, "Stale.txt", b"stale upload", other)
            assert stale["category_id"] == other
            response = client.patch(
                picture["manage_url"] + "category/", json={"category_id": other}, headers=headers
            )
            assert response.status_code == 200
            response = client.patch(
                picture["manage_url"] + "category/", json={"category_id": source}, headers=headers
            )
            assert response.json()["attachment"]["category_id"] == target
            rejected = client.patch(
                stale["manage_url"] + "category/", json={"category_id": target}, headers=headers
            )
            assert (
                rejected.status_code == 409
                and rejected.json()["error"]["code"] == "category_in_use"
            )
            assert app.state.vehicles.get_attachment(car.id, stale["id"]).category_id == other
            try:
                with connection.transaction():
                    connection.execute(
                        "UPDATE limo_attachment SET category_id=%s WHERE id=%s",
                        (target, stale["id"]),
                    )
            except UniqueViolation as error:
                assert error.diag.constraint_name == "hspace_vehicle_category_unique"
            else:
                raise AssertionError(
                    "Database category guard did not reject duplicate classification."
                )
            try:
                with connection.transaction():
                    connection.execute(
                        "UPDATE limo_attachment SET is_deleted=FALSE,deleted_at=NULL,deleted_by=NULL WHERE id=%s",
                        (deleted["id"],),
                    )
            except UniqueViolation as error:
                assert error.diag.constraint_name == "hspace_vehicle_category_unique"
            else:
                raise AssertionError(
                    "Database category guard did not reject duplicate restoration."
                )

            assert (
                client.patch(
                    deleted["manage_url"] + "category/",
                    json={"category_id": target},
                    headers=headers,
                ).status_code
                == 404
            )
            assert (
                client.patch(
                    f'/api/vehicles/{missing_car.id}/attachments/{picture["id"]}/category/',
                    json={"category_id": target},
                    headers=headers,
                ).status_code
                == 404
            )
            assert (
                client.patch(
                    driver["manage_url"] + "category/",
                    json={"category_id": target},
                    headers=headers,
                ).status_code
                == 200
            )
            assert (
                client.patch(
                    office["manage_url"] + "category/",
                    json={"category_id": target},
                    headers=headers,
                ).status_code
                == 404
            )
            availability = post(
                "/api/attachment-download/availability/",
                {"vehicle_ids": [car.id, missing_car.id], "category_ids": [target]},
            )
            assert availability["file_count"] == 1
            by_vehicle = {row["id"]: row for row in availability["vehicles"]}
            assert by_vehicle[car.id]["documents"] == [{"category_id": target, "count": 1}]
            assert by_vehicle[missing_car.id]["documents"] == [{"category_id": target, "count": 0}]
            empty_status = post(
                "/api/attachment-download/availability/",
                {
                    "vehicle_ids": [car.id, missing_car.id],
                    "category_ids": [
                        next(item["id"] for item in initial if item["code"] == "direction_card")
                    ],
                },
            )
            assert empty_status["file_count"] == 0 and len(empty_status["vehicles"]) == 2
            assert client.get("/api/attachment-categories/").json()["categories"][-1]["is_other"]
            response = client.post(
                "/api/attachment-download/",
                json={"vehicle_ids": [car.id, missing_car.id], "category_ids": [target, other]},
                headers=headers,
            )
            assert response.status_code == 200
            assert response.headers["X-HSpace-File-Count"] == "4"
            assert response.headers["X-HSpace-Missing-Count"] == "2"
            assert "no-store" in response.headers["cache-control"]
            with ZipFile(io.BytesIO(response.content)) as archive:
                folder = car.plate_number + "/"
                assert set(archive.namelist()) == {
                    folder + "Picture.png",
                    folder + "Document.pdf",
                    folder + "Notes.txt",
                    folder + "Stale.txt",
                    "_missing-documents.txt",
                }
                assert archive.read(folder + "Picture.png") == image_bytes
                assert archive.read(folder + "Document.pdf") == pdf_bytes
                assert archive.read(folder + "Notes.txt") == b"original notes"
                assert missing_car.plate_number in archive.read("_missing-documents.txt").decode(
                    "utf-8-sig"
                )
            assert client.get(pdf["download_url"]).content == pdf_bytes
            different_car_file = upload(
                f"/api/vehicles/{missing_car.id}/attachments/",
                "Separate.txt",
                b"separate vehicle",
                source,
            )
            assert different_car_file["category_id"] == target
            assert client.delete(f"/api/vehicles/{car.id}/", headers=headers).status_code == 204
            post(
                "/api/attachment-download/",
                {"vehicle_ids": [car.id], "category_ids": [target]},
                404,
            )
            events = connection.execute(
                "SELECT action,actor_id FROM hspace_activity WHERE entity_kind='category' AND entity_id=ANY(%s)",
                ([source, target],),
            ).fetchall()
            assert {"CREATE", "ALIAS", "MERGE"} <= {event["action"] for event in events}
            assert all(event["actor_id"] == operator.id for event in events)
        finally:
            connection.rollback()
    assert snapshot() == original_records
    assert media_manifest(settings.media_root) == originals
    print(
        "PASS: operator category/alias/merge, duplicate guards, stale uploads, all attachment scopes, deleted-file retention, ZIP originals grouped by plate and missing documents. Fixture rows rolled back; originals unchanged; sequences may advance."
    )


if __name__ == "__main__":
    main()
