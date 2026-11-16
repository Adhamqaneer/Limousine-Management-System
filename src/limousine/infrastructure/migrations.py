"""Transactional versioned PostgreSQL schema for FastAPI."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
from limousine.config.runtime import ROOT

DDL = """
CREATE TABLE IF NOT EXISTS hspace_schema_migration (version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS limo_vehicle (
 id bigserial PRIMARY KEY, plate_number varchar(64) NOT NULL,
 vehicle_type varchar(120) NOT NULL DEFAULT '', driver_name varchar(200) NOT NULL DEFAULT '',
 chassis_number varchar(120) NOT NULL DEFAULT '', manufacture_year varchar(32) NOT NULL DEFAULT '',
 created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS limo_attachment (
 id bigserial PRIMARY KEY, vehicle_id bigint NOT NULL REFERENCES limo_vehicle(id) ON DELETE CASCADE,
 storage_key varchar(500) NOT NULL, original_name varchar(255) NOT NULL,
 kind varchar(5) NOT NULL CHECK(kind IN ('image','file')), size bigint NOT NULL CHECK(size>0),
 created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS hspace_attachment_vehicle_idx ON limo_attachment(vehicle_id);
CREATE TABLE IF NOT EXISTS limo_vehicle_cover (
 id bigserial PRIMARY KEY, vehicle_id bigint NOT NULL UNIQUE REFERENCES limo_vehicle(id) ON DELETE CASCADE,
 storage_key varchar(500) NOT NULL, original_name varchar(255) NOT NULL, size bigint NOT NULL CHECK(size>0));
CREATE TABLE IF NOT EXISTS hspace_user (
 id uuid PRIMARY KEY, slot smallint NOT NULL UNIQUE CHECK(slot BETWEEN 1 AND 4),
 username varchar(150) NOT NULL UNIQUE, password_hash varchar(256) NOT NULL,
 role varchar(10) NOT NULL CHECK(role IN ('ADMIN','MEMBER')), is_active boolean NOT NULL DEFAULT TRUE,
 is_deleted boolean NOT NULL DEFAULT FALSE, deleted_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP, last_login timestamptz,
 CHECK ((is_deleted AND deleted_at IS NOT NULL AND NOT is_active) OR (NOT is_deleted AND deleted_at IS NULL)));
CREATE UNIQUE INDEX IF NOT EXISTS hspace_single_admin ON hspace_user(role) WHERE role='ADMIN';
CREATE TABLE IF NOT EXISTS hspace_session (
 token_hash char(64) PRIMARY KEY, user_id uuid NOT NULL REFERENCES hspace_user(id) ON DELETE CASCADE,
 expires_at timestamptz NOT NULL);
CREATE INDEX IF NOT EXISTS hspace_session_user_idx ON hspace_session(user_id);
"""
def media_manifest(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in Path(root).rglob("*") if path.is_file()} if Path(root).exists() else {}

def backup_database(settings):
    directory = ROOT / ".local/backups"
    directory.mkdir(parents=True, exist_ok=True)
    executable = shutil.which("pg_dump") or ("C:/Program Files/PostgreSQL/18/bin/pg_dump.exe" if os.name == "nt" else None)
    if not executable or not Path(executable).is_file():
        raise RuntimeError("Install PostgreSQL pg_dump before migrating existing data.")
    target = directory / ("before-fastapi-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + ".dump")
    environment = os.environ.copy()
    environment["PGPASSWORD"] = settings.db_password
    result = subprocess.run([executable, "-h", settings.db_host, "-p", settings.db_port,
        "-U", settings.db_user, "-d", settings.db_name, "-Fc", "-f", str(target)],
        env=environment, capture_output=True, timeout=120)
    if result.returncode or not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError("PostgreSQL backup failed. No schema changes were applied.")
    return target

def migrate(database):
    settings = database.settings
    if settings.db_host not in ("127.0.0.1", "localhost", "::1") or settings.db_name != "limousine_local":
        raise ValueError("Local migrations are restricted to the configured limousine_local database.")
    with database.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(72730804)")
        connection.execute(DDL)
        connection.execute("INSERT INTO hspace_schema_migration(version) VALUES (1) ON CONFLICT DO NOTHING")
    return None
