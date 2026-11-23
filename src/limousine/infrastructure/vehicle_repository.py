"""PostgreSQL implementation of the framework-independent vehicle contract."""

from psycopg import sql

from limousine.domain.attachments import AttachmentNameConflict
from limousine.domain.recycling import require_actor, validate_kind
from limousine.domain.vehicles import (
    Attachment,
    DomainError,
    NotFound,
    Vehicle,
    VehicleCover,
)
from limousine.infrastructure.categories import (
    PostgresCategoryRepository,
    ensure_vehicle_category_available,
    resolve_upload_category,
)
from limousine.infrastructure.drivers import seed_driver
from limousine.infrastructure.media_paths import vehicle_directory


def attachment(row):
    return Attachment(
        row["id"],
        row["vehicle_id"],
        row["storage_key"],
        row["original_name"],
        row["kind"],
        row["size"],
        row["created_at"],
        row.get("driver_assignment_id"),
        row.get("category_id"),
    )


class PostgresVehicleRepository:
    def __init__(self, database, media_layout=None):
        self.database = database
        self.media_layout = media_layout

    def _vehicle(self, connection, row):
        attachments = connection.execute(
            """
                SELECT *
                FROM limo_attachment
                WHERE vehicle_id=%s
                  AND driver_assignment_id IS NULL
                  AND NOT is_deleted
                ORDER BY id
            """,
            (row["id"],),
        ).fetchall()
        photo = connection.execute(
            "SELECT * FROM limo_vehicle_cover WHERE vehicle_id=%s AND NOT is_deleted", (row["id"],)
        ).fetchone()
        return self._build_vehicle(row, attachments, photo)

    @staticmethod
    def _build_vehicle(row, attachments, photo):
        return Vehicle(
            row["id"],
            row["plate_number"],
            row["created_at"],
            tuple(attachment(item) for item in attachments),
            row["vehicle_type"],
            row["driver_name"],
            row["chassis_number"],
            row["manufacture_year"],
            (
                VehicleCover(row["id"], photo["storage_key"], photo["original_name"], photo["size"])
                if photo
                else None
            ),
            owner_name=row["owner_name"],
            owner_phone=row["owner_phone"],
            driver_phone=row["driver_phone"],
        )

    def list_vehicles(self):
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM limo_vehicle WHERE NOT is_deleted ORDER BY id"
            ).fetchall()
            if not rows:
                return []
            ids = [row["id"] for row in rows]
            attachments = {vehicle_id: [] for vehicle_id in ids}
            for item in connection.execute(
                """
                    SELECT *
                    FROM limo_attachment
                    WHERE vehicle_id=ANY(%s)
                      AND driver_assignment_id IS NULL
                      AND NOT is_deleted
                    ORDER BY id
                """,
                (ids,),
            ).fetchall():
                attachments[item["vehicle_id"]].append(item)
            covers = {
                item["vehicle_id"]: item
                for item in connection.execute(
                    "SELECT * FROM limo_vehicle_cover WHERE vehicle_id=ANY(%s) AND NOT is_deleted",
                    (ids,),
                ).fetchall()
            }
            return [
                self._build_vehicle(row, attachments[row["id"]], covers.get(row["id"]))
                for row in rows
            ]

    def get_vehicle(self, vehicle_id):
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM limo_vehicle WHERE id=%s AND NOT is_deleted", (vehicle_id,)
            ).fetchone()
            if not row:
                raise NotFound("Vehicle not found.")
            return self._vehicle(connection, row)

    def create_vehicle(self, plate_number, *, actor=None, **fields):
        values = {
            "plate_number": plate_number,
            "vehicle_type": "",
            "driver_name": "",
            "chassis_number": "",
            "manufacture_year": "",
            **fields,
        }
        values["created_by"] = actor.id if actor else None
        with self.database.connect() as connection:
            query = sql.SQL(
                "INSERT INTO limo_vehicle ({},created_at) VALUES ({},CURRENT_TIMESTAMP) RETURNING *"
            ).format(
                sql.SQL(",").join(map(sql.Identifier, values)),
                sql.SQL(",").join(sql.Placeholder() for _ in values),
            )
            row = connection.execute(query, tuple(values.values())).fetchone()
            seed_driver(connection, row, actor)
            if self.media_layout:
                self.media_layout.ensure_sections(vehicle_directory(row["id"]), covers=True)
            if actor:
                self._event(
                    connection,
                    actor,
                    "vehicle",
                    row["id"],
                    row["id"],
                    "CREATE",
                    row["plate_number"],
                )
            return self._vehicle(connection, row)

    def update_vehicle(self, vehicle_id, **fields):
        with self.database.connect() as connection:
            query = sql.SQL(
                "UPDATE limo_vehicle SET {} WHERE id=%s AND NOT is_deleted RETURNING id"
            ).format(
                sql.SQL(",").join(sql.SQL("{}=%s").format(sql.Identifier(name)) for name in fields)
            )
            if not connection.execute(query, (*fields.values(), vehicle_id)).fetchone():
                raise NotFound("Vehicle not found.")
        return self.get_vehicle(vehicle_id)

    def add_attachment(self, vehicle_id, *, actor=None, assignment_id=None, **metadata):
        with self.database.connect() as connection:
            category_id = resolve_upload_category(connection, metadata.get("category_id"))
            self._lock_vehicle(connection, vehicle_id)
            self._check_assignment(connection, vehicle_id, assignment_id)
            if assignment_id is None:
                ensure_vehicle_category_available(connection, vehicle_id, category_id)
            row = connection.execute(
                """
                    INSERT INTO limo_attachment (vehicle_id,
                                   storage_key, original_name, kind, size, created_at, created_by,
                                   driver_assignment_id, category_id)
                    VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,%s,%s,COALESCE(%s,(SELECT id FROM hspace_attachment_category WHERE is_other))) RETURNING *
                """,
                (
                    vehicle_id,
                    metadata["storage_key"],
                    metadata["original_name"],
                    metadata["kind"],
                    metadata["size"],
                    actor.id if actor else None,
                    assignment_id,
                    category_id,
                ),
            ).fetchone()
            if actor:
                self._event(
                    connection,
                    actor,
                    "attachment",
                    row["id"],
                    vehicle_id,
                    "CREATE",
                    row["original_name"],
                )
            return attachment(row)

    def get_attachment(self, vehicle_id, attachment_id, *, assignment_id=None):
        with self.database.connect() as connection:
            row = connection.execute(
                """
                    SELECT a.*
                    FROM limo_attachment a
                    JOIN limo_vehicle v ON v.id=a.vehicle_id
                    WHERE a.vehicle_id=%s
                      AND a.id=%s
                      AND a.driver_assignment_id IS NOT DISTINCT
                      FROM %s
                      AND NOT a.is_deleted
                      AND NOT v.is_deleted
                """,
                (vehicle_id, attachment_id, assignment_id),
            ).fetchone()
            if not row:
                raise NotFound("Attachment not found.")
            return attachment(row)

    @staticmethod
    def _check_assignment(connection, vehicle_id, assignment_id):
        if (
            assignment_id is not None
            and not connection.execute(
                "SELECT id FROM hspace_driver_assignment WHERE id=%s AND vehicle_id=%s",
                (assignment_id, vehicle_id),
            ).fetchone()
        ):
            raise NotFound("Driver period not found for this vehicle.")

    def driver_attachments(self, vehicle_id, assignment_id):
        with self.database.connect() as connection:
            if not connection.execute(
                "SELECT id FROM limo_vehicle WHERE id=%s AND NOT is_deleted", (vehicle_id,)
            ).fetchone():
                raise NotFound("Vehicle not found.")
            self._check_assignment(connection, vehicle_id, assignment_id)
            return [
                attachment(row)
                for row in connection.execute(
                    "SELECT * FROM limo_attachment WHERE vehicle_id=%s AND driver_assignment_id=%s AND NOT is_deleted ORDER BY id",
                    (vehicle_id, assignment_id),
                ).fetchall()
            ]

    @staticmethod
    def _lock_vehicle(connection, vehicle_id, *, deleted=False):
        row = connection.execute(
            "SELECT * FROM limo_vehicle WHERE id=%s AND is_deleted=%s FOR UPDATE",
            (vehicle_id, deleted),
        ).fetchone()
        if not row:
            raise NotFound("Vehicle not found.")
        return row

    @staticmethod
    def _event(connection, actor, kind, item_id, vehicle_id, action, label, reason=""):
        require_actor(actor)
        connection.execute(
            """
                INSERT INTO hspace_activity(vehicle_id,
                              entity_kind, entity_id, action, actor_id, actor_name, label, reason)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (vehicle_id, kind, item_id, action, actor.id, actor.username, label, reason),
        )

    def replace_cover(self, cover, *, actor=None):
        require_actor(actor)
        with self.database.connect() as connection:
            self._lock_vehicle(connection, cover.vehicle_id)
            old = connection.execute(
                "SELECT * FROM limo_vehicle_cover WHERE vehicle_id=%s AND NOT is_deleted FOR UPDATE",
                (cover.vehicle_id,),
            ).fetchone()
            if old:
                connection.execute(
                    "UPDATE limo_vehicle_cover SET is_deleted=TRUE,deleted_at=CURRENT_TIMESTAMP,deleted_by=%s WHERE id=%s",
                    (actor.id, old["id"]),
                )
                self._event(
                    connection,
                    actor,
                    "cover",
                    old["id"],
                    cover.vehicle_id,
                    "DELETE",
                    old["original_name"],
                    "replaced",
                )
            row = connection.execute(
                """
                    INSERT INTO limo_vehicle_cover(vehicle_id,
                                  storage_key, original_name, size, created_by)
                    VALUES (%s,%s,%s,%s,%s) RETURNING id
                """,
                (cover.vehicle_id, cover.storage_key, cover.original_name, cover.size, actor.id),
            ).fetchone()
            self._event(
                connection,
                actor,
                "cover",
                row["id"],
                cover.vehicle_id,
                "CREATE",
                cover.original_name,
            )
            return cover, None

    def delete_vehicle(self, vehicle_id, actor):
        require_actor(actor)
        with self.database.connect() as connection:
            row = self._lock_vehicle(connection, vehicle_id)
            connection.execute(
                "UPDATE limo_vehicle SET is_deleted=TRUE,deleted_at=CURRENT_TIMESTAMP,deleted_by=%s WHERE id=%s",
                (actor.id, vehicle_id),
            )
            self._event(
                connection, actor, "vehicle", vehicle_id, vehicle_id, "DELETE", row["plate_number"]
            )

    def delete_attachment(self, vehicle_id, attachment_id, *, actor, assignment_id=None):
        require_actor(actor)
        with self.database.connect() as connection:
            self._lock_vehicle(connection, vehicle_id)
            row = connection.execute(
                """
                    UPDATE limo_attachment
                    SET is_deleted=TRUE,deleted_at=CURRENT_TIMESTAMP,deleted_by=%s
                    WHERE vehicle_id=%s
                      AND id=%s
                      AND driver_assignment_id IS NOT DISTINCT
                      FROM %s
                      AND NOT is_deleted RETURNING id,original_name
                """,
                (actor.id, vehicle_id, attachment_id, assignment_id),
            ).fetchone()
            if not row:
                raise NotFound("Attachment not found for this vehicle.")
            self._event(
                connection,
                actor,
                "attachment",
                row["id"],
                vehicle_id,
                "DELETE",
                row["original_name"],
            )

    def delete_cover(self, vehicle_id, *, actor):
        require_actor(actor)
        with self.database.connect() as connection:
            self._lock_vehicle(connection, vehicle_id)
            row = connection.execute(
                """
                    UPDATE limo_vehicle_cover
                    SET is_deleted=TRUE,deleted_at=CURRENT_TIMESTAMP,deleted_by=%s
                    WHERE vehicle_id=%s
                      AND NOT is_deleted RETURNING id,original_name
                """,
                (actor.id, vehicle_id),
            ).fetchone()
            if not row:
                raise NotFound("Card photo not found.")
            self._event(
                connection, actor, "cover", row["id"], vehicle_id, "DELETE", row["original_name"]
            )

    def rename_attachment(
        self, vehicle_id, attachment_id, original_name, *, expected_name, actor, assignment_id=None
    ):
        require_actor(actor)
        with self.database.connect() as connection:
            self._lock_vehicle(connection, vehicle_id)
            row = connection.execute(
                """
                    SELECT *
                    FROM limo_attachment
                    WHERE vehicle_id=%s
                      AND id=%s
                      AND driver_assignment_id IS NOT DISTINCT
                      FROM %s
                      AND NOT is_deleted
                      FOR
                      UPDATE
                """,
                (vehicle_id, attachment_id, assignment_id),
            ).fetchone()
            if not row:
                raise NotFound("Attachment not found for this vehicle.")
            if row["original_name"] != expected_name:
                raise AttachmentNameConflict("The attachment name changed. Refresh and try again.")
            if original_name == row["original_name"]:
                return attachment(row)
            updated = connection.execute(
                "UPDATE limo_attachment SET original_name=%s WHERE vehicle_id=%s AND id=%s AND NOT is_deleted RETURNING *",
                (original_name, vehicle_id, attachment_id),
            ).fetchone()
            self._event(
                connection, actor, "attachment", attachment_id, vehicle_id, "RENAME", original_name
            )
            return attachment(updated)

    def list_deleted(self):
        result = []
        with self.database.connect() as connection:
            for kind, table in [
                ("vehicle", "limo_vehicle"),
                ("attachment", "limo_attachment"),
                ("cover", "limo_vehicle_cover"),
            ]:
                parent = "t.id" if kind == "vehicle" else "t.vehicle_id"
                label = "t.plate_number" if kind == "vehicle" else "t.original_name"
                driver = (
                    "(SELECT driver_name FROM hspace_driver_assignment WHERE id=t.driver_assignment_id)"
                    if kind == "attachment"
                    else "NULL::text"
                )
                query = sql.SQL(
                    "SELECT t.id,{} AS label,{} AS driver_name, v.id AS vehicle_id,v.plate_number, v.is_deleted AS parent_deleted,EXISTS(SELECT 1 FROM limo_vehicle_cover current_photo WHERE current_photo.vehicle_id=v.id AND NOT current_photo.is_deleted) AS has_current_cover,t.created_at,t.deleted_at,c.username AS created_by,d.username AS deleted_by FROM {} t JOIN limo_vehicle v ON v.id={} LEFT JOIN hspace_user c ON c.id=t.created_by LEFT JOIN hspace_user d ON d.id=t.deleted_by WHERE t.is_deleted ORDER BY t.deleted_at DESC,t.id DESC"
                ).format(sql.SQL(label), sql.SQL(driver), sql.Identifier(table), sql.SQL(parent))
                for row in connection.execute(query).fetchall():
                    result.append(dict(row, kind=kind))
        from .office import PostgresOfficeRepository

        result.extend(PostgresOfficeRepository(self.database).list_deleted())
        return sorted(result, key=lambda row: row["deleted_at"], reverse=True)

    def restore_item(self, kind, item_id, actor):
        require_actor(actor)
        validate_kind(kind)
        if kind == "office":
            from .office import PostgresOfficeRepository

            return PostgresOfficeRepository(self.database).restore(item_id, actor)
        table = {
            "vehicle": "limo_vehicle",
            "attachment": "limo_attachment",
            "cover": "limo_vehicle_cover",
        }[kind]
        with self.database.connect() as connection:
            PostgresCategoryRepository._lock(connection)
            if kind == "vehicle":
                row = self._lock_vehicle(connection, item_id, deleted=True)
                vehicle_id = item_id
            else:
                item = connection.execute(
                    sql.SQL("SELECT vehicle_id FROM {} WHERE id=%s AND is_deleted").format(
                        sql.Identifier(table)
                    ),
                    (item_id,),
                ).fetchone()
                if not item:
                    raise NotFound("Deleted item not found.")
                vehicle_id = item["vehicle_id"]
                # Parent first for consistent lock ordering across all file mutations.
                self._lock_vehicle(connection, vehicle_id)
                row = connection.execute(
                    sql.SQL("SELECT * FROM {} WHERE id=%s AND is_deleted FOR UPDATE").format(
                        sql.Identifier(table)
                    ),
                    (item_id,),
                ).fetchone()
                if not row:
                    raise NotFound("Deleted item not found.")
                if (
                    kind == "cover"
                    and connection.execute(
                        "SELECT 1 FROM limo_vehicle_cover WHERE vehicle_id=%s AND NOT is_deleted",
                        (vehicle_id,),
                    ).fetchone()
                ):
                    raise DomainError(
                        "Remove the current card photo before restoring an older photo."
                    )
            if kind == "attachment" and row["driver_assignment_id"] is None:
                ensure_vehicle_category_available(
                    connection, vehicle_id, row["category_id"], item_id
                )
            connection.execute(
                sql.SQL(
                    "UPDATE {} SET is_deleted=FALSE,deleted_at=NULL,deleted_by=NULL WHERE id=%s"
                ).format(sql.Identifier(table)),
                (item_id,),
            )
            self._event(
                connection,
                actor,
                kind,
                item_id,
                vehicle_id,
                "RESTORE",
                row["plate_number"] if kind == "vehicle" else row["original_name"],
            )

    def list_activity(self, before=None):
        with self.database.connect() as connection:
            return connection.execute(
                """
                    SELECT a.id,a.vehicle_id,a.entity_kind,a.entity_id,a.action,a.actor_name,a.label,a.reason,
                           a.created_at,v.plate_number,d.driver_name
                    FROM hspace_activity a
                    LEFT JOIN limo_vehicle v ON v.id=a.vehicle_id
                    LEFT JOIN limo_attachment f ON a.entity_kind='attachment'
                    AND f.id=a.entity_id
                    LEFT JOIN hspace_driver_assignment d ON d.id=f.driver_assignment_id
                    WHERE (%s::bigint IS NULL
                           OR a.id<%s)
                    ORDER BY a.id DESC
                    LIMIT 100
                """,
                (before, before),
            ).fetchall()
