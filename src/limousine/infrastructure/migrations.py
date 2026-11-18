"""Transactional versioned PostgreSQL schema for FastAPI."""

import hashlib
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from psycopg import sql

from limousine.config.runtime import ROOT
from limousine.infrastructure.media_paths import (
    VEHICLE_FILE_PATTERN,
    COVER_FILE_PATTERN,
    OFFICE_FILE_PATTERN,
    STORAGE_KEY_PATTERN,
)

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
    return (
        {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in Path(root).rglob("*")
            if path.is_file()
        }
        if Path(root).exists()
        else {}
    )


def backup_database(settings):
    directory = ROOT / ".local/backups"
    directory.mkdir(parents=True, exist_ok=True)
    executable = shutil.which("pg_dump") or (
        "C:/Program Files/PostgreSQL/18/bin/pg_dump.exe" if os.name == "nt" else None
    )
    if not executable or not Path(executable).is_file():
        raise RuntimeError("Install PostgreSQL pg_dump before migrating existing data.")
    target = directory / (
        "before-fastapi-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + ".dump"
    )
    environment = os.environ.copy()
    environment["PGPASSWORD"] = settings.db_password
    result = subprocess.run(
        [
            executable,
            "-h",
            settings.db_host,
            "-p",
            settings.db_port,
            "-U",
            settings.db_user,
            "-d",
            settings.db_name,
            "-Fc",
            "-f",
            str(target),
        ],
        env=environment,
        capture_output=True,
        timeout=120,
    )
    if result.returncode or not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError("PostgreSQL backup failed. No schema changes were applied.")
    return target


def migrate(database):
    settings = database.settings
    if (
        settings.db_host not in ("127.0.0.1", "localhost", "::1")
        or settings.db_name != "limousine_local"
    ):
        raise ValueError(
            "Local migrations are restricted to the configured limousine_local database."
        )
    with database.connect() as connection:
        exists = connection.execute(
            "SELECT to_regclass('public.hspace_schema_migration') AS name"
        ).fetchone()["name"]
        upgrade = (
            exists
            and not connection.execute(
                "SELECT 1 FROM hspace_schema_migration WHERE version=9"
            ).fetchone()
        )
    backup = backup_database(settings) if upgrade else None
    with database.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(72730804)")
        connection.execute(DDL)
        connection.execute(
            "INSERT INTO hspace_schema_migration(version) VALUES (1) ON CONFLICT DO NOTHING"
        )
        if not connection.execute(
            "SELECT 1 FROM hspace_schema_migration WHERE version=2"
        ).fetchone():
            connection.execute("""
                CREATE TABLE hspace_file_cleanup (
                    storage_key varchar(500) PRIMARY KEY,
                    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CHECK (storage_key ~ '^vehicles/[0-9a-f]{32}[.](jpg|jpeg|png|webp|pdf|txt|docx|xlsx)$'));
                ALTER TABLE limo_vehicle ADD CONSTRAINT hspace_vehicle_required_fields
                    CHECK (btrim(plate_number) <> '' AND btrim(vehicle_type) <> '');
                ALTER TABLE limo_attachment ADD CONSTRAINT hspace_attachment_kind
                    CHECK (kind IN ('image','file'));
                ALTER TABLE hspace_user ADD CONSTRAINT hspace_username_not_blank CHECK (btrim(username) <> '');
                ALTER TABLE hspace_session ADD CONSTRAINT hspace_session_hash_format CHECK (token_hash ~ '^[0-9a-f]{64}$');
                CREATE INDEX hspace_session_expiry_idx ON hspace_session(expires_at);
            """)
            for table in ("limo_attachment", "limo_vehicle_cover"):
                connection.execute(
                    sql.SQL(
                        "ALTER TABLE {} ADD CONSTRAINT {} CHECK (size > 0 AND size <= 10485760 AND btrim(original_name) <> '')"
                    ).format(sql.Identifier(table), sql.Identifier(table + "_valid_metadata"))
                )
                connection.execute(
                    sql.SQL(
                        "ALTER TABLE {} ADD CONSTRAINT {} CHECK (storage_key ~ '^vehicles/[0-9a-f]{{32}}[.](jpg|jpeg|png|webp|pdf|txt|docx|xlsx)$')"
                    ).format(sql.Identifier(table), sql.Identifier(table + "_valid_key"))
                )
                connection.execute(
                    sql.SQL("ALTER TABLE {} ADD CONSTRAINT {} UNIQUE(storage_key)").format(
                        sql.Identifier(table), sql.Identifier(table + "_storage_key_unique")
                    )
                )
                # Replace the obsolete nonnegative check with the stronger bounded check.
                connection.execute(
                    sql.SQL("ALTER TABLE {} DROP CONSTRAINT IF EXISTS {}").format(
                        sql.Identifier(table), sql.Identifier(table + "_size_check")
                    )
                )
            # An inherited index duplicated hspace_attachment_vehicle_idx.
            connection.execute("DROP INDEX IF EXISTS limo_attachment_vehicle_id_155e7f20")
            connection.execute("INSERT INTO hspace_schema_migration(version) VALUES (2)")
        if not connection.execute(
            "SELECT 1 FROM hspace_schema_migration WHERE version=3"
        ).fetchone():
            connection.execute("""
                ALTER TABLE limo_vehicle
                    ADD COLUMN owner_name varchar(200) NOT NULL DEFAULT '',
                    ADD COLUMN owner_phone varchar(32) NOT NULL DEFAULT '',
                    ADD COLUMN driver_phone varchar(32) NOT NULL DEFAULT '',
                    ADD CONSTRAINT hspace_owner_phone_digits CHECK (owner_phone !~ '[^0-9\u0660-\u0669\u06f0-\u06f9]'),
                    ADD CONSTRAINT hspace_driver_phone_digits CHECK (driver_phone !~ '[^0-9]');
                INSERT INTO hspace_schema_migration(version) VALUES (3);
            """)
        if not connection.execute(
            "SELECT 1 FROM hspace_schema_migration WHERE version=4"
        ).fetchone():
            for table in ("limo_vehicle", "limo_attachment", "limo_vehicle_cover"):
                connection.execute(
                    sql.SQL(
                        """ALTER TABLE {} ADD COLUMN created_by uuid REFERENCES hspace_user(id),
                    ADD COLUMN is_deleted boolean NOT NULL DEFAULT FALSE,
                    ADD COLUMN deleted_at timestamptz,
                    ADD COLUMN deleted_by uuid REFERENCES hspace_user(id),
                    ADD CONSTRAINT {} CHECK ((is_deleted AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL)
                        OR (NOT is_deleted AND deleted_at IS NULL AND deleted_by IS NULL))"""
                    ).format(sql.Identifier(table), sql.Identifier(table + "_deletion_state"))
                )
            # Retain older cover versions; only one undeleted cover may be active.
            constraints = connection.execute(
                """SELECT conname FROM pg_constraint
                WHERE conrelid='limo_vehicle_cover'::regclass AND contype='u'
                AND conkey=ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid='limo_vehicle_cover'::regclass AND attname='vehicle_id')]::smallint[]"""
            ).fetchall()
            for constraint in constraints:
                connection.execute(
                    sql.SQL("ALTER TABLE limo_vehicle_cover DROP CONSTRAINT {}").format(
                        sql.Identifier(constraint["conname"])
                    )
                )
            connection.execute("""
                ALTER TABLE limo_vehicle_cover ADD COLUMN created_at timestamptz;
                ALTER TABLE limo_vehicle_cover ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
                CREATE UNIQUE INDEX hspace_one_active_cover ON limo_vehicle_cover(vehicle_id) WHERE NOT is_deleted;
                CREATE INDEX hspace_deleted_vehicles ON limo_vehicle(deleted_at) WHERE is_deleted;
                CREATE TABLE hspace_activity (
                    id bigserial PRIMARY KEY, vehicle_id bigint NOT NULL REFERENCES limo_vehicle(id),
                    entity_kind varchar(10) NOT NULL CHECK(entity_kind IN ('vehicle','attachment','cover')),
                    entity_id bigint NOT NULL, action varchar(10) NOT NULL CHECK(action IN ('CREATE','DELETE','RESTORE')),
                    actor_id uuid NOT NULL REFERENCES hspace_user(id), actor_name varchar(150) NOT NULL,
                    label varchar(255) NOT NULL, reason varchar(20) NOT NULL DEFAULT '',
                    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX hspace_activity_vehicle_idx ON hspace_activity(vehicle_id,id DESC);
                CREATE FUNCTION hspace_retain_records() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'Retained records cannot be physically removed.' USING ERRCODE='23514'; END $$;
                CREATE TRIGGER hspace_retain_vehicle BEFORE DELETE ON limo_vehicle FOR EACH ROW EXECUTE FUNCTION hspace_retain_records();
                CREATE TRIGGER hspace_retain_attachment BEFORE DELETE ON limo_attachment FOR EACH ROW EXECUTE FUNCTION hspace_retain_records();
                CREATE TRIGGER hspace_retain_cover BEFORE DELETE ON limo_vehicle_cover FOR EACH ROW EXECUTE FUNCTION hspace_retain_records();
                CREATE TRIGGER hspace_retain_activity BEFORE UPDATE OR DELETE ON hspace_activity FOR EACH ROW EXECUTE FUNCTION hspace_retain_records();
                INSERT INTO hspace_schema_migration(version) VALUES (4);
            """)
        if not connection.execute(
            "SELECT 1 FROM hspace_schema_migration WHERE version=5"
        ).fetchone():
            connection.execute("""
                CREATE TABLE hspace_driver_assignment (
                    id bigserial PRIMARY KEY, vehicle_id bigint NOT NULL REFERENCES limo_vehicle(id),
                    driver_name varchar(200) NOT NULL, driver_phone varchar(32) NOT NULL DEFAULT '',
                    started_on date, ended_on date, is_current boolean NOT NULL DEFAULT TRUE,
                    created_by uuid REFERENCES hspace_user(id), created_by_name varchar(150),
                    created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
                    updated_by uuid REFERENCES hspace_user(id), updated_by_name varchar(150), updated_at timestamptz,
                    CHECK((is_current AND ended_on IS NULL) OR (NOT is_current AND ended_on IS NOT NULL)),
                    CHECK(started_on IS NULL OR ended_on IS NULL OR started_on<=ended_on));
                CREATE UNIQUE INDEX hspace_driver_current ON hspace_driver_assignment(vehicle_id) WHERE is_current;
                CREATE INDEX hspace_driver_vehicle ON hspace_driver_assignment(vehicle_id,id DESC);
                CREATE TABLE hspace_driver_change (
                    id bigserial PRIMARY KEY, vehicle_id bigint NOT NULL REFERENCES limo_vehicle(id),
                    assignment_id bigint NOT NULL REFERENCES hspace_driver_assignment(id),
                    action varchar(8) NOT NULL CHECK(action IN ('ASSIGN','CORRECT')),
                    actor_id uuid NOT NULL REFERENCES hspace_user(id), actor_name varchar(150) NOT NULL,
                    before_data jsonb, after_data jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX hspace_driver_change_vehicle ON hspace_driver_change(vehicle_id,id DESC);
                INSERT INTO hspace_driver_assignment(vehicle_id,driver_name,driver_phone,created_at)
                    SELECT id,driver_name,driver_phone,NULL FROM limo_vehicle WHERE driver_name<>'' OR driver_phone<>'';
                CREATE TRIGGER hspace_retain_driver BEFORE DELETE ON hspace_driver_assignment FOR EACH ROW EXECUTE FUNCTION hspace_retain_records();
                CREATE TRIGGER hspace_retain_driver_change BEFORE UPDATE OR DELETE ON hspace_driver_change FOR EACH ROW EXECUTE FUNCTION hspace_retain_records();
                CREATE FUNCTION hspace_driver_current_guard() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN
                    IF (NEW.driver_name,NEW.driver_phone) IS DISTINCT FROM (OLD.driver_name,OLD.driver_phone)
                        AND NOT EXISTS(SELECT 1 FROM hspace_driver_assignment a WHERE a.vehicle_id=NEW.id AND a.is_current
                            AND a.driver_name=NEW.driver_name AND a.driver_phone=NEW.driver_phone)
                    THEN RAISE EXCEPTION 'Use the driver history workflow.' USING ERRCODE='23514'; END IF;
                    RETURN NEW;
                END $$;
                CREATE TRIGGER hspace_guard_current_driver BEFORE UPDATE OF driver_name,driver_phone ON limo_vehicle
                    FOR EACH ROW EXECUTE FUNCTION hspace_driver_current_guard();
                INSERT INTO hspace_schema_migration(version) VALUES (5);
            """)
        if not connection.execute(
            "SELECT 1 FROM hspace_schema_migration WHERE version=6"
        ).fetchone():
            connection.execute("""
                ALTER TABLE hspace_activity DROP CONSTRAINT hspace_activity_action_check;
                ALTER TABLE hspace_activity ADD CONSTRAINT hspace_activity_action_check
                    CHECK(action IN ('CREATE','DELETE','RESTORE','RENAME'));
                INSERT INTO hspace_schema_migration(version) VALUES (6);
            """)
        if not connection.execute(
            "SELECT 1 FROM hspace_schema_migration WHERE version=7"
        ).fetchone():
            connection.execute("""
                ALTER TABLE hspace_driver_assignment ADD CONSTRAINT hspace_driver_vehicle_identity UNIQUE(id,vehicle_id);
                ALTER TABLE limo_attachment ADD COLUMN driver_assignment_id bigint,
                    ADD CONSTRAINT hspace_attachment_driver FOREIGN KEY(driver_assignment_id,vehicle_id)
                        REFERENCES hspace_driver_assignment(id,vehicle_id);
                CREATE INDEX hspace_driver_attachments ON limo_attachment(driver_assignment_id,id) WHERE driver_assignment_id IS NOT NULL;
                ALTER TABLE hspace_driver_change DROP CONSTRAINT hspace_driver_change_action_check;
                ALTER TABLE hspace_driver_change ADD CONSTRAINT hspace_driver_change_action_check CHECK(action IN ('ASSIGN','CORRECT','END'));
                CREATE OR REPLACE FUNCTION hspace_driver_current_guard() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN
                    IF (NEW.driver_name,NEW.driver_phone) IS DISTINCT FROM (OLD.driver_name,OLD.driver_phone)
                        AND NOT ((NEW.driver_name='' AND NEW.driver_phone='' AND NOT EXISTS(
                            SELECT 1 FROM hspace_driver_assignment a WHERE a.vehicle_id=NEW.id AND a.is_current))
                        OR EXISTS(SELECT 1 FROM hspace_driver_assignment a WHERE a.vehicle_id=NEW.id AND a.is_current
                            AND a.driver_name=NEW.driver_name AND a.driver_phone=NEW.driver_phone))
                    THEN RAISE EXCEPTION 'Use the driver history workflow.' USING ERRCODE='23514'; END IF;
                    RETURN NEW;
                END $$;
                INSERT INTO hspace_schema_migration(version) VALUES (7);
            """)
        if not connection.execute(
            "SELECT 1 FROM hspace_schema_migration WHERE version=8"
        ).fetchone():
            connection.execute("""
                CREATE TABLE hspace_office_attachment (
                    id bigserial PRIMARY KEY,
                    storage_key varchar(500) NOT NULL UNIQUE CHECK(storage_key ~ '^office/[0-9a-f]{32}[.](jpg|jpeg|png|webp|pdf|txt|docx|xlsx)$'),
                    original_name varchar(180) NOT NULL CHECK(btrim(original_name) <> ''),
                    kind varchar(5) NOT NULL CHECK(kind IN ('image','file')),
                    size bigint NOT NULL CHECK(size>0 AND size<=10485760),
                    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by uuid NOT NULL REFERENCES hspace_user(id),
                    is_deleted boolean NOT NULL DEFAULT FALSE,
                    deleted_at timestamptz, deleted_by uuid REFERENCES hspace_user(id),
                    CONSTRAINT hspace_office_deletion_state CHECK((is_deleted AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL)
                        OR (NOT is_deleted AND deleted_at IS NULL AND deleted_by IS NULL)));
                CREATE INDEX hspace_office_deleted ON hspace_office_attachment(deleted_at) WHERE is_deleted;
                CREATE TRIGGER hspace_retain_office BEFORE DELETE ON hspace_office_attachment FOR EACH ROW EXECUTE FUNCTION hspace_retain_records();
                ALTER TABLE hspace_activity ALTER COLUMN vehicle_id DROP NOT NULL;
                ALTER TABLE hspace_activity DROP CONSTRAINT hspace_activity_entity_kind_check;
                ALTER TABLE hspace_activity ADD CONSTRAINT hspace_activity_entity_kind_check CHECK(entity_kind IN ('vehicle','attachment','cover','office'));
                ALTER TABLE hspace_activity ADD CONSTRAINT hspace_activity_scope CHECK(
                    (entity_kind='office' AND vehicle_id IS NULL) OR (entity_kind<>'office' AND vehicle_id IS NOT NULL));
                ALTER TABLE hspace_file_cleanup DROP CONSTRAINT hspace_file_cleanup_storage_key_check;
                ALTER TABLE hspace_file_cleanup ADD CONSTRAINT hspace_file_cleanup_storage_key_check
                    CHECK(storage_key ~ '^(vehicles|office)/[0-9a-f]{32}[.](jpg|jpeg|png|webp|pdf|txt|docx|xlsx)$');
                INSERT INTO hspace_schema_migration(version) VALUES (8);
            """)
        if not connection.execute(
            "SELECT 1 FROM hspace_schema_migration WHERE version=9"
        ).fetchone():
            constraints = (
                ("limo_attachment", "limo_attachment_valid_key", VEHICLE_FILE_PATTERN),
                ("limo_vehicle_cover", "limo_vehicle_cover_valid_key", COVER_FILE_PATTERN),
                (
                    "hspace_file_cleanup",
                    "hspace_file_cleanup_storage_key_check",
                    STORAGE_KEY_PATTERN,
                ),
            )
            # The office key constraint was originally named automatically by PostgreSQL.
            office_constraints = connection.execute("""
                SELECT conname FROM pg_constraint
                WHERE conrelid='hspace_office_attachment'::regclass AND contype='c'
                  AND pg_get_constraintdef(oid) LIKE '%storage_key%'
            """).fetchall()
            for constraint in office_constraints:
                connection.execute(
                    sql.SQL("ALTER TABLE hspace_office_attachment DROP CONSTRAINT {}").format(
                        sql.Identifier(constraint["conname"])
                    )
                )
            for table, name, pattern in constraints:
                connection.execute(
                    sql.SQL("ALTER TABLE {} DROP CONSTRAINT {}").format(
                        sql.Identifier(table), sql.Identifier(name)
                    )
                )
                connection.execute(
                    sql.SQL("ALTER TABLE {} ADD CONSTRAINT {} CHECK(storage_key ~ {})").format(
                        sql.Identifier(table), sql.Identifier(name), sql.Literal(pattern)
                    )
                )
            connection.execute(
                sql.SQL(
                    "ALTER TABLE hspace_office_attachment ADD CONSTRAINT hspace_office_valid_key CHECK(storage_key ~ {})"
                ).format(sql.Literal(OFFICE_FILE_PATTERN))
            )
            connection.execute("INSERT INTO hspace_schema_migration(version) VALUES (9)")
    return backup
