"""Read-only local database and private-file integrity audit; no row contents."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from limousine.config.runtime import load_settings
    from limousine.domain.accounts import OPERATOR_USERNAME
    from limousine.infrastructure.attachments import LocalAttachmentStore
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.migrations import SCHEMA_VERSION

    settings = load_settings()
    if (
        settings.db_host not in ("127.0.0.1", "localhost", "::1")
        or settings.db_name != "limousine_local"
    ):
        raise ValueError("Audit requires the intended local database.")
    database, store = Database(settings), LocalAttachmentStore(settings.media_root)
    with database.connect() as connection:
        # A consistent read-only database snapshot; no fixture writes or cleanup.
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        counts = {
            table: connection.execute("SELECT count(*) AS n FROM " + table).fetchone()["n"]
            for table in (
                "limo_vehicle",
                "limo_attachment",
                "limo_vehicle_cover",
                "hspace_user",
                "hspace_operator",
                "hspace_session",
                "hspace_file_cleanup",
                "hspace_activity",
                "hspace_driver_assignment",
                "hspace_driver_change",
                "hspace_office_attachment",
                "hspace_attachment_category",
                "hspace_category_alias",
            )
        }
        report = {"counts": counts}
        report["office_account_ready"] = counts["hspace_operator"] == 1 and bool(
            connection.execute(
                "SELECT 1 FROM hspace_operator o JOIN hspace_user u ON u.id=o.user_id WHERE u.username=%s",
                (OPERATOR_USERNAME,),
            ).fetchone()
        )
        role = connection.execute(
            "SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user"
        ).fetchone()
        report["restricted_database_role"] = not any(role.values())
        report["unvalidated_constraints"] = connection.execute(
            "SELECT count(*) AS n FROM pg_constraint WHERE connamespace='public'::regnamespace AND NOT convalidated"
        ).fetchone()["n"]
        keys = connection.execute(
            "SELECT storage_key,size FROM limo_attachment UNION ALL SELECT storage_key,size FROM limo_vehicle_cover UNION ALL SELECT storage_key,size FROM hspace_office_attachment"
        ).fetchall()
        pending = {
            row["storage_key"]
            for row in connection.execute("SELECT storage_key FROM hspace_file_cleanup").fetchall()
        }
        missing = {
            "hspace_office_deleted",
            "hspace_one_other_category",
            "hspace_alias_category",
            "hspace_attachment_category_idx",
            "hspace_office_category_idx",
            "hspace_driver_attachments",
            "hspace_one_active_cover",
            "hspace_activity_vehicle_idx",
            "hspace_deleted_vehicles",
            "hspace_attachment_vehicle_idx",
            "hspace_session_user_idx",
            "hspace_session_expiry_idx",
            "limo_attachment_storage_key_unique",
            "limo_vehicle_cover_storage_key_unique",
        }
        missing -= {
            row["indexname"]
            for row in connection.execute(
                "SELECT indexname FROM pg_indexes WHERE schemaname='public'"
            ).fetchall()
        }
        report["missing_required_indexes"] = sorted(missing)
        constraints = {
            row["conname"]
            for row in connection.execute(
                "SELECT conname FROM pg_constraint WHERE connamespace='public'::regnamespace"
            ).fetchall()
        }
        report["missing_required_constraints"] = sorted(
            {
                "hspace_activity_scope",
                "hspace_office_deletion_state",
                "hspace_attachment_driver",
                "hspace_driver_vehicle_identity",
                "hspace_owner_phone_digits",
                "hspace_driver_phone_digits",
                "hspace_vehicle_required_fields",
                "hspace_attachment_kind",
                "limo_attachment_valid_metadata",
                "limo_vehicle_cover_valid_metadata",
                "limo_attachment_valid_key",
                "limo_vehicle_cover_valid_key",
                "hspace_session_hash_format",
                "hspace_session_operator_fk",
            }
            - constraints
        )
        report["schema_versions"] = [
            row["version"]
            for row in connection.execute(
                "SELECT version FROM hspace_schema_migration ORDER BY version"
            ).fetchall()
        ]
        report["missing_retention_triggers"] = sorted(
            {
                "hspace_retain_office",
                "hspace_vehicle_category_unique",
                "hspace_retain_category",
                "hspace_retain_category_alias",
                "hspace_retain_vehicle",
                "hspace_retain_attachment",
                "hspace_retain_cover",
                "hspace_retain_activity",
            }
            - {
                row["tgname"]
                for row in connection.execute(
                    "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgenabled='O'"
                )
            }
        )
        report["missing_deletion_constraints"] = sorted(
            (
                {"hspace_office_deletion_state"}
                | {
                    table + "_deletion_state"
                    for table in ("limo_vehicle", "limo_attachment", "limo_vehicle_cover")
                }
            )
            - constraints
        )
        report["missing_driver_triggers"] = sorted(
            {"hspace_retain_driver", "hspace_retain_driver_change", "hspace_guard_current_driver"}
            - {
                row["tgname"]
                for row in connection.execute(
                    "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgenabled='O'"
                )
            }
        )
        report["driver_state_mismatches"] = connection.execute(
            """SELECT count(*) AS n FROM limo_vehicle v LEFT JOIN hspace_driver_assignment a ON a.vehicle_id=v.id AND a.is_current
            WHERE (a.id IS NULL AND (v.driver_name<>'' OR v.driver_phone<>'')) OR (a.id IS NOT NULL AND (v.driver_name<>a.driver_name OR v.driver_phone<>a.driver_phone))"""
        ).fetchone()["n"]
        report["deleted_counts"] = {
            table: connection.execute(
                "SELECT count(*) AS n FROM " + table + " WHERE is_deleted"
            ).fetchone()["n"]
            for table in (
                "limo_vehicle",
                "limo_attachment",
                "limo_vehicle_cover",
                "hspace_office_attachment",
            )
        }
    missing_files = invalid_keys = size_mismatch = 0
    for row in keys:
        try:
            path = store.path(row["storage_key"])
        except FileNotFoundError:
            invalid_keys += 1
            continue
        if not path.is_file():
            missing_files += 1
        elif path.stat().st_size != row["size"]:
            size_mismatch += 1
    actual = (
        {
            path.relative_to(store.root).as_posix()
            for path in store.root.rglob("*")
            if path.is_file()
        }
        if store.root.exists()
        else set()
    )
    report["files"] = {
        "missing": missing_files,
        "invalid_keys": invalid_keys,
        "size_mismatch": size_mismatch,
        "unreferenced_without_cleanup_entry": len(
            actual - {row["storage_key"] for row in keys} - pending
        ),
    }
    report["ok"] = (
        report["restricted_database_role"]
        and report["office_account_ready"]
        and not report["unvalidated_constraints"]
        and not missing
        and not report["missing_required_constraints"]
        and not any(report["files"].values())
        and not report["missing_retention_triggers"]
        and not report["missing_deletion_constraints"]
        and not report["missing_driver_triggers"]
        and not report["driver_state_mismatches"]
        and report["schema_versions"] == list(range(1, SCHEMA_VERSION + 1))
    )
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Database audit failed ({type(error).__name__}); private details suppressed.")
        raise SystemExit(1)
