"""One normalized-name registry prevents canonical/alias races and preserves merges."""

from limousine.domain.categories import (
    CategoryConflict,
    SimilarCategory,
    category_key,
    require_free_category,
    similar_categories,
)
from limousine.domain.vehicles import DomainError, NotFound

CATEGORY_LOCK_ID = 72730806


class PostgresCategoryRepository:
    def __init__(
        self,
        database,
    ):
        self.database = database

    @staticmethod
    def _lock(connection):
        connection.execute(
            "SELECT pg_advisory_xact_lock(%s)",
            (CATEGORY_LOCK_ID,),
        )

    @staticmethod
    def _resolve(
        connection,
        category_id,
    ):
        seen = set()
        while category_id not in seen:
            seen.add(category_id)
            row = connection.execute(
                "SELECT * FROM hspace_attachment_category WHERE id=%s",
                (category_id,),
            ).fetchone()
            if not row:
                raise NotFound("Category not found.")
            if row["merged_into"] is None:
                return row
            category_id = row["merged_into"]
        raise DomainError("The category merge chain is invalid.")

    @staticmethod
    def _categories(connection):
        return connection.execute("""
            SELECT c.id,c.name,c.code,c.is_other,
                   COALESCE((SELECT json_agg(a.name ORDER BY a.id) FROM hspace_category_alias a
                             WHERE a.category_id=c.id AND a.name<>c.name),'[]'::json) AS aliases,
                   (SELECT count(*) FROM limo_attachment f WHERE f.category_id=c.id) +
                   (SELECT count(*) FROM hspace_office_attachment f WHERE f.category_id=c.id) AS attachment_count
            FROM hspace_attachment_category c WHERE c.merged_into IS NULL
            ORDER BY c.is_other,c.id
        """).fetchall()

    @staticmethod
    def _event(
        connection,
        actor,
        category_id,
        action,
        label,
    ):
        connection.execute(
            """
            INSERT INTO hspace_activity(vehicle_id,entity_kind,entity_id,action,actor_id,actor_name,label)
            VALUES (NULL,'category',%s,%s,%s,%s,%s)
        """,
            (category_id, action, actor.id, actor.username, label),
        )

    def list_categories(
        self,
        query="",
    ):
        with self.database.connect() as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            categories = self._categories(connection)
            links = {
                row["id"]: row["merged_into"]
                for row in connection.execute(
                    "SELECT id,merged_into FROM hspace_attachment_category"
                ).fetchall()
            }
            redirects = {}
            for source, target in links.items():
                if target is None:
                    continue
                seen = {source}
                while (
                    links.get(target) is not None
                    and target not in seen
                ):
                    seen.add(target)
                    target = links[target]
                redirects[source] = target
            exact = None
            suggestions = []
            if query:
                key = category_key(query)
                alias = connection.execute(
                    "SELECT category_id FROM hspace_category_alias WHERE normalized_name=%s",
                    (key,),
                ).fetchone()
                if alias:
                    exact = alias["category_id"]
                suggestions = [
                    item["id"]
                    for item in similar_categories(
                        categories,
                        query,
                    )
                ]
            return {
                "categories": categories,
                "exact_id": exact,
                "similar_ids": suggestions,
                "redirects": redirects,
            }

    def get(
        self,
        category_id,
    ):
        with self.database.connect() as connection:
            return self._resolve(
                connection,
                category_id,
            )

    def create(
        self,
        name,
        key,
        actor,
        allow_similar=False,
    ):
        with self.database.connect() as connection:
            self._lock(connection)
            alias = connection.execute(
                "SELECT category_id FROM hspace_category_alias WHERE normalized_name=%s",
                (key,),
            ).fetchone()
            if alias:
                return self._resolve(
                    connection,
                    alias["category_id"],
                )
            if (
                not allow_similar
                and similar_categories(
                self._categories(connection),
                name,
            )
            ):
                raise SimilarCategory(
                    "Review the similar categories before adding a distinct type."
                )
            row = connection.execute(
                "INSERT INTO hspace_attachment_category(name,created_by) VALUES (%s,%s) RETURNING *",
                (name, actor.id),
            ).fetchone()
            connection.execute(
                "INSERT INTO hspace_category_alias(category_id,name,normalized_name) VALUES (%s,%s,%s)",
                (row["id"], name, key),
            )
            self._event(
                connection,
                actor,
                row["id"],
                "CREATE",
                name,
            )
            return row

    def add_alias(
        self,
        category_id,
        name,
        key,
        actor,
    ):
        with self.database.connect() as connection:
            self._lock(connection)
            category = self._resolve(
                connection,
                category_id,
            )
            if category["is_other"]:
                raise DomainError("Other cannot absorb named document types.")
            existing = connection.execute(
                "SELECT category_id FROM hspace_category_alias WHERE normalized_name=%s",
                (key,),
            ).fetchone()
            if existing:
                if existing["category_id"] != category["id"]:
                    raise CategoryConflict(
                        "This name already belongs to another category. Use merge instead."
                    )
                return category
            connection.execute(
                "INSERT INTO hspace_category_alias(category_id,name,normalized_name) VALUES (%s,%s,%s)",
                (category["id"], name, key),
            )
            self._event(
                connection,
                actor,
                category["id"],
                "ALIAS",
                name + " → " + category["name"],
            )
            return category

    def merge(
        self,
        source_id,
        target_id,
        actor,
    ):
        with self.database.connect() as connection:
            self._lock(connection)
            source = self._resolve(
                connection,
                source_id,
            )
            target = self._resolve(
                connection,
                target_id,
            )
            if (
                source["id"] != source_id
                or target["id"] != target_id
            ):
                raise CategoryConflict("A category changed. Refresh before merging.")
            if (
                source_id == target_id
                or source["is_other"]
                or target["is_other"]
            ):
                raise DomainError("Choose two different named categories. Other cannot be merged.")
            connection.execute(
                "UPDATE limo_attachment SET category_id=%s WHERE category_id=%s",
                (target_id, source_id),
            )
            connection.execute(
                "UPDATE hspace_category_alias SET category_id=%s WHERE category_id=%s",
                (target_id, source_id),
            )
            connection.execute(
                "UPDATE hspace_attachment_category SET merged_into=%s WHERE id=%s",
                (target_id, source_id),
            )
            self._event(
                connection,
                actor,
                source_id,
                "MERGE",
                source["name"] + " → " + target["name"],
            )
            return target

    def classify(
        self,
        vehicle_id,
        attachment_id,
        category_id,
        actor,
        assignment_id=None,
    ):
        with self.database.connect() as connection:
            self._lock(connection)
            category = self._resolve(
                connection,
                category_id,
            )
            if not connection.execute(
                "SELECT id FROM limo_vehicle WHERE id=%s AND NOT is_deleted FOR UPDATE",
                (vehicle_id,),
            ).fetchone():
                raise NotFound("Vehicle not found.")
            row = connection.execute(
                """
                SELECT * FROM limo_attachment
                WHERE id=%s AND vehicle_id=%s AND driver_assignment_id IS NOT DISTINCT FROM %s
                  AND NOT is_deleted
                FOR UPDATE
                """,
                (attachment_id, vehicle_id, assignment_id),
            ).fetchone()
            if not row:
                raise NotFound("Attachment not found.")
            if row["category_id"] != category["id"]:
                if assignment_id is None:
                    ensure_vehicle_category_available(
                        connection,
                        vehicle_id,
                        category["id"],
                        attachment_id,
                    )
                row = connection.execute(
                    "UPDATE limo_attachment SET category_id=%s WHERE id=%s RETURNING *",
                    (category["id"], attachment_id),
                ).fetchone()
                connection.execute(
                    """
                    INSERT INTO hspace_activity(
                        vehicle_id, entity_kind, entity_id, action, actor_id, actor_name, label
                    )
                    VALUES (%s,'attachment',%s,'LABEL',%s,%s,%s)
                    """,
                    (
                        vehicle_id,
                        attachment_id,
                        actor.id,
                        actor.username,
                        (row["original_name"] + " → " + category["name"])[:255],
                    ),
                )
            return row


def resolve_upload_category(
    connection,
    category_id,
):
    """Resolve stale upload selections under the same lock used for merges."""
    PostgresCategoryRepository._lock(connection)
    if category_id is None:
        return None
    return PostgresCategoryRepository._resolve(
        connection,
        category_id,
    )["id"]


def ensure_vehicle_category_available(
    connection,
    vehicle_id,
    category_id,
    exclude_id=None,
):
    """Caller holds category/vehicle locks; Photos and Files share the same slot."""
    if category_id is None:
        return
    category = connection.execute(
        "SELECT is_other FROM hspace_attachment_category WHERE id=%s",
        (category_id,),
    ).fetchone()
    if not category:
        raise NotFound("Category not found.")
    occupied = connection.execute(
        """SELECT 1 FROM limo_attachment
        WHERE vehicle_id=%s AND category_id=%s AND driver_assignment_id IS NULL
          AND NOT is_deleted AND id IS DISTINCT FROM %s LIMIT 1""",
        (vehicle_id, category_id, exclude_id),
    ).fetchone()
    require_free_category(
        category["is_other"],
        bool(occupied),
    )
