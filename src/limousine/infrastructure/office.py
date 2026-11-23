"""PostgreSQL office metadata and atomic actor-attributed lifecycle events."""

from limousine.domain.attachments import AttachmentNameConflict
from limousine.domain.office import OfficeAttachment
from limousine.domain.recycling import require_actor
from limousine.domain.vehicles import NotFound


def attachment(row):
    return OfficeAttachment(
        **{
            key: row[key]
            for key in ("id", "storage_key", "original_name", "kind", "size", "created_at")
        }
    )


class PostgresOfficeRepository:
    def __init__(
        self,
        database,
    ):
        self.database = database

    @staticmethod
    def _event(
        connection,
        actor,
        row,
        action,
    ):
        require_actor(actor)
        connection.execute(
            """
                INSERT INTO hspace_activity(vehicle_id,
                              entity_kind, entity_id, action, actor_id, actor_name, label)
                VALUES (NULL,'office',%s,%s,%s,%s,%s)
            """,
            (row["id"], action, actor.id, actor.username, row["original_name"]),
        )

    def list_files(self):
        with self.database.connect() as connection:
            return [
                attachment(row)
                for row in connection.execute(
                    "SELECT * FROM hspace_office_attachment WHERE NOT is_deleted ORDER BY id"
                ).fetchall()
            ]

    def get(
        self,
        item_id,
    ):
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM hspace_office_attachment WHERE id=%s AND NOT is_deleted",
                (item_id,),
            ).fetchone()
            if not row:
                raise NotFound("Office attachment not found.")
            return attachment(row)

    def add(
        self,
        storage_key,
        original_name,
        kind,
        size,
        actor,
    ):
        require_actor(actor)
        with self.database.connect() as connection:
            row = connection.execute(
                """
                    INSERT INTO hspace_office_attachment(storage_key,
                                  original_name, kind, size, created_by)
                    VALUES (%s,%s,%s,%s,%s) RETURNING *
                """,
                (storage_key, original_name, kind, size, actor.id),
            ).fetchone()
            self._event(
                connection,
                actor,
                row,
                "CREATE",
            )
            return attachment(row)

    def rename(
        self,
        item_id,
        name,
        expected_name,
        actor,
    ):
        require_actor(actor)
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM hspace_office_attachment WHERE id=%s AND NOT is_deleted FOR UPDATE",
                (item_id,),
            ).fetchone()
            if not row:
                raise NotFound("Office attachment not found.")
            if row["original_name"] != expected_name:
                raise AttachmentNameConflict("The attachment name changed. Refresh and try again.")
            if row["original_name"] == name:
                return attachment(row)
            row = connection.execute(
                "UPDATE hspace_office_attachment SET original_name=%s WHERE id=%s RETURNING *",
                (name, item_id),
            ).fetchone()
            self._event(
                connection,
                actor,
                row,
                "RENAME",
            )
            return attachment(row)

    def delete(
        self,
        item_id,
        actor,
    ):
        require_actor(actor)
        with self.database.connect() as connection:
            row = connection.execute(
                """
                    UPDATE hspace_office_attachment
                    SET is_deleted=TRUE,deleted_at=CURRENT_TIMESTAMP,deleted_by=%s
                    WHERE id=%s
                      AND NOT is_deleted RETURNING *
                """,
                (actor.id, item_id),
            ).fetchone()
            if not row:
                raise NotFound("Office attachment not found.")
            self._event(
                connection,
                actor,
                row,
                "DELETE",
            )

    def restore(
        self,
        item_id,
        actor,
    ):
        require_actor(actor)
        with self.database.connect() as connection:
            row = connection.execute(
                """
                    UPDATE hspace_office_attachment
                    SET is_deleted=FALSE,deleted_at=NULL,deleted_by=NULL
                    WHERE id=%s
                      AND is_deleted RETURNING *
                """,
                (item_id,),
            ).fetchone()
            if not row:
                raise NotFound("Deleted office attachment not found.")
            self._event(
                connection,
                actor,
                row,
                "RESTORE",
            )

    def list_deleted(self):
        with self.database.connect() as connection:
            return connection.execute("""
                    SELECT t.id,
                           'office' AS kind,
                           t.original_name AS label,
                           NULL::text AS driver_name,
                           NULL::bigint AS vehicle_id,
                           NULL::text AS plate_number,
                           FALSE AS parent_deleted,
                           FALSE AS has_current_cover,
                           t.created_at,
                           t.deleted_at,
                           c.username AS created_by,
                           d.username AS deleted_by
                    FROM hspace_office_attachment t
                    LEFT JOIN hspace_user c ON c.id=t.created_by
                    LEFT JOIN hspace_user d ON d.id=t.deleted_by
                    WHERE t.is_deleted
                    ORDER BY t.deleted_at DESC,t.id DESC
                """).fetchall()
