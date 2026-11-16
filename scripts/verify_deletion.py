"""Real PostgreSQL deletion checks using only temporary records and files."""
from dataclasses import replace
import io
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    import psycopg
    from fastapi.testclient import TestClient
    from PIL import Image
    from limousine.config.runtime import load_settings
    from limousine.infrastructure.accounts import token_hash
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.migrations import media_manifest
    from limousine.presentation.web.app import create_app
    settings = load_settings()
    assert settings.db_host in ("127.0.0.1", "localhost", "::1") and settings.db_name == "limousine_local"
    db = Database(settings)
    tables = ("limo_vehicle", "limo_attachment", "limo_vehicle_cover", "hspace_user")
    with db.connect() as c:
        baseline = {name: c.execute("SELECT * FROM " + name + " ORDER BY id").fetchall() for name in tables}
        member = c.execute("SELECT id FROM hspace_user WHERE role='MEMBER' AND is_active AND NOT is_deleted ORDER BY slot LIMIT 1").fetchone()
    assert member
    original_files = media_manifest(settings.media_root)
    ids, keys, sessions = [], [], []
    with TemporaryDirectory(prefix="hspace-deletion-") as media:
        app = create_app(replace(settings, media_root=Path(media), allowed_hosts=("testserver",)))
        client, anonymous = TestClient(app), TestClient(app)
        try:
            token = app.state.accounts.create_session(member["id"], 300)
            sessions.append(token_hash(token))
            client.cookies.set("hspace_session", token)
            client.get("/")
            headers = {"X-CSRFToken": client.cookies["csrftoken"]}
            def create_car():
                car = client.post("/api/vehicles/", json={"plate_number": "DELETE-TEST", "vehicle_type": "Temporary test"}, headers=headers).json()["vehicle"]
                ids.append(car["id"])
                return f'/api/vehicles/{car["id"]}/'
            url, other = create_car(), create_car()
            image = io.BytesIO(); Image.new("RGB", (2, 2), "white").save(image, "PNG")
            photo = client.post(url + "attachments/", files={"file": ("photo.png", image.getvalue())}, headers=headers).json()["attachment"]
            document = client.post(url + "attachments/", files={"file": ("document.txt", b"Temporary file")}, headers=headers).json()["attachment"]
            assert client.post(url + "cover/", files={"file": ("cover.png", image.getvalue())}, headers=headers).status_code == 201
            with db.connect() as c:
                keys.extend(row["storage_key"] for row in c.execute("SELECT storage_key FROM limo_attachment WHERE vehicle_id=ANY(%s) UNION ALL SELECT storage_key FROM limo_vehicle_cover WHERE vehicle_id=ANY(%s)", (ids, ids)).fetchall())
                old_cover = c.execute("SELECT storage_key FROM limo_vehicle_cover WHERE vehicle_id=%s", (ids[0],)).fetchone()["storage_key"]
            assert client.post(url + "cover/", files={"file": ("replacement.png", image.getvalue())}, headers=headers).status_code == 201
            with db.connect() as c:
                keys.append(c.execute("SELECT storage_key FROM limo_vehicle_cover WHERE vehicle_id=%s", (ids[0],)).fetchone()["storage_key"])
            assert not app.state.store.path(old_cover).exists()
            endpoint = url + f'attachments/{photo["id"]}/'
            assert anonymous.delete(endpoint).status_code == 401
            assert client.delete(endpoint).status_code == 403
            assert client.delete(other + f'attachments/{photo["id"]}/', headers=headers).status_code == 404
            assert client.get(photo["preview_url"]).status_code == 200
            assert client.delete(endpoint, headers=headers).status_code == 204
            assert client.delete(endpoint, headers=headers).status_code == 404
            assert client.get(photo["preview_url"]).status_code == 404
            assert client.get(photo["download_url"]).status_code == 404
            assert client.get(url + "cover/").status_code == 200
            assert client.get(document["preview_url"]).status_code == 200
            assert client.get(url).json()["vehicle"]["attachment_count"] == 1
            assert client.delete(url + "cover/", headers=headers).status_code == 204
            assert client.get(url).json()["vehicle"]["cover_url"] is None
            assert client.get(document["preview_url"]).status_code == 200
            endpoint = url + f'attachments/{document["id"]}/'
            # A database failure must roll back metadata AND its cleanup entry.
            with patch.object(app.state.vehicles.repository, "_queue_cleanup", side_effect=psycopg.OperationalError("private")):
                assert client.delete(endpoint, headers=headers).status_code == 503
            assert client.get(document["preview_url"]).status_code == 200
            with patch.object(app.state.store, "delete", side_effect=PermissionError()):
                assert client.delete(endpoint, headers=headers).status_code == 204
            assert client.get(document["preview_url"]).status_code == 404
            with db.connect() as c:
                pending = c.execute("SELECT storage_key FROM hspace_file_cleanup WHERE storage_key=ANY(%s)", (keys,)).fetchall()
            assert len(pending) == 1 and app.state.store.path(pending[0]["storage_key"]).is_file()
            assert app.state.cleanup.process(pending[0]["storage_key"])
            assert not list(Path(media).rglob("*.txt")) and not list(Path(media).rglob("*.png"))
            # Probe actual constraints; every unsuccessful probe rolls back.
            probes = [
                ("UPDATE limo_vehicle SET plate_number='' WHERE id=%s", (ids[0],)),
                ("INSERT INTO limo_attachment(vehicle_id,storage_key,original_name,kind,size,created_at) VALUES(%s,%s,'test','wrong',1,CURRENT_TIMESTAMP)", (ids[0], keys[0])),
                ("INSERT INTO limo_attachment(vehicle_id,storage_key,original_name,kind,size,created_at) VALUES(%s,%s,'test','file',0,CURRENT_TIMESTAMP)", (ids[0], keys[0])),
                ("INSERT INTO limo_attachment(vehicle_id,storage_key,original_name,kind,size,created_at) VALUES(%s,'../escape.txt','test','file',1,CURRENT_TIMESTAMP)", (ids[0],)),
                ("INSERT INTO limo_attachment(vehicle_id,storage_key,original_name,kind,size,created_at) VALUES(-1,%s,'test','file',1,CURRENT_TIMESTAMP)", (keys[0],)),
            ]
            for statement, parameters in probes:
                try:
                    with db.connect() as c: c.execute(statement, parameters)
                except psycopg.IntegrityError:
                    pass
                else:
                    raise AssertionError("Database accepted invalid metadata.")
            try:
                with db.connect() as c:
                    statement = "INSERT INTO limo_attachment(vehicle_id,storage_key,original_name,kind,size,created_at) VALUES(%s,%s,'test','file',1,CURRENT_TIMESTAMP)"
                    c.execute(statement, (ids[0], keys[0]))
                    c.execute(statement, (ids[0], keys[0]))
            except psycopg.IntegrityError:
                pass
            else:
                raise AssertionError("Database accepted a duplicate storage key.")
        finally:
            with db.connect() as c:
                c.execute("DELETE FROM hspace_file_cleanup WHERE storage_key=ANY(%s)", (keys,))
                c.execute("DELETE FROM limo_vehicle_cover WHERE vehicle_id=ANY(%s)", (ids,))
                c.execute("DELETE FROM limo_attachment WHERE vehicle_id=ANY(%s)", (ids,))
                c.execute("DELETE FROM limo_vehicle WHERE id=ANY(%s)", (ids,))
                c.execute("DELETE FROM hspace_session WHERE token_hash=ANY(%s)", (sessions,))
                # Test session creation updates last_login; restore that field only.
                for row in baseline["hspace_user"]:
                    if row["id"] == member["id"]:
                        c.execute("UPDATE hspace_user SET last_login=%s WHERE id=%s", (row["last_login"], row["id"]))
    with db.connect() as c:
        for name in tables:
            assert baseline[name] == c.execute("SELECT * FROM " + name + " ORDER BY id").fetchall()
    assert original_files == media_manifest(settings.media_root)
    print("PASS: member deletion, authentication/CSRF, vehicle scoping, repeat deletion, private previews and independent cover.")
    print("PASS: database rollback, deferred disk cleanup/retry and actual metadata CHECK constraints.")
    print("Existing accounts, business rows and file bytes unchanged; test fixtures removed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Deletion verification failed ({type(error).__name__}); private details suppressed.")
        raise SystemExit(1)
