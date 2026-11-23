"""Transactional driver periods; flat current fields remain synchronized for reports."""

from contextlib import nullcontext

from psycopg.types.json import Jsonb

from limousine.domain.drivers import DriverValidationError, validate_boundary
from limousine.domain.vehicles import DomainError, NotFound


def driver_snapshot(row):
    if not row:
        return None
    return {
        "driver_name": row["driver_name"],
        "driver_phone": row["driver_phone"],
        "started_on": row["started_on"].isoformat() if row["started_on"] else None,
        "ended_on": row["ended_on"].isoformat() if row.get("ended_on") else None,
        "is_current": row.get(
            "is_current",
            True,
        ),
    }


def seed_driver(
    connection,
    vehicle,
    actor=None,
):
    if (
        vehicle["driver_name"]
        or vehicle["driver_phone"]
    ):
        row = connection.execute(
            """

                INSERT INTO hspace_driver_assignment(vehicle_id,
                              driver_name, driver_phone, created_by, created_by_name)
                VALUES (%s,%s,%s,%s,%s) RETURNING *
            """,
            (
                vehicle["id"],
                vehicle["driver_name"],
                vehicle["driver_phone"],
                actor.id if actor else None,
                actor.username if actor else None,
            ),
        ).fetchone()
        if actor:
            record_driver_change(
                connection,
                vehicle["id"],
                row["id"],
                "ASSIGN",
                actor,
                None,
                row,
            )


def record_driver_change(
    connection,
    vehicle_id,
    assignment_id,
    action,
    actor,
    before,
    after,
):
    connection.execute(
        """

            INSERT INTO hspace_driver_change(vehicle_id,
                          assignment_id, action, actor_id, actor_name, before_data, after_data)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            vehicle_id,
            assignment_id,
            action,
            actor.id,
            actor.username,
            Jsonb(driver_snapshot(before)),
            Jsonb(driver_snapshot(after)),
        ),
    )


class PostgresDriverRepository:
    def __init__(
        self,
        database,
        media_layout=None,
    ):
        self.database = database
        self.media_layout = media_layout

    def _media_operation(self):
        return self.media_layout.operation() if self.media_layout else nullcontext()

    def change_driver(
        self,
        vehicle_id,
        details,
        started_on,
        actor,
        *,
        correcting=False,
    ):
        with self._media_operation(), self.database.connect() as connection:
            if not connection.execute(
                "SELECT id FROM limo_vehicle WHERE id=%s AND NOT is_deleted FOR UPDATE",
                (vehicle_id,),
            ).fetchone():
                raise NotFound("Vehicle not found.")
            current_assignment = connection.execute(
                "SELECT * FROM hspace_driver_assignment WHERE vehicle_id=%s AND is_current FOR UPDATE",
                (vehicle_id,),
            ).fetchone()
            previous_end = connection.execute(
                "SELECT max(ended_on) AS ended_on FROM hspace_driver_assignment WHERE vehicle_id=%s AND NOT is_current",
                (vehicle_id,),
            ).fetchone()["ended_on"]
            validate_boundary(
                started_on,
                current_assignment["started_on"] if current_assignment else None,
                previous_end,
                correcting=correcting,
            )
            if correcting:
                if not current_assignment:
                    raise DomainError("There is no current driver to correct. Use Change driver.")
                row = connection.execute(
                    """

                        UPDATE hspace_driver_assignment
                        SET driver_name=%s,driver_phone=%s,started_on=%s,updated_by=%s,updated_by_name=%s,updated_at=CURRENT_TIMESTAMP
                        WHERE id=%s RETURNING *
                    """,
                    (
                        details["driver_name"],
                        details["driver_phone"],
                        started_on,
                        actor.id,
                        actor.username,
                        current_assignment["id"],
                    ),
                ).fetchone()
            else:
                if current_assignment:
                    connection.execute(
                        "UPDATE hspace_driver_assignment SET is_current=FALSE,ended_on=%s WHERE id=%s",
                        (started_on, current_assignment["id"]),
                    )
                row = connection.execute(
                    """

                        INSERT INTO hspace_driver_assignment(vehicle_id,
                                      driver_name, driver_phone, started_on, created_by, created_by_name)
                        VALUES (%s,%s,%s,%s,%s,%s) RETURNING *
                    """,
                    (
                        vehicle_id,
                        details["driver_name"],
                        details["driver_phone"],
                        started_on,
                        actor.id,
                        actor.username,
                    ),
                ).fetchone()
            connection.execute(
                "UPDATE limo_vehicle SET driver_name=%s,driver_phone=%s WHERE id=%s",
                (details["driver_name"], details["driver_phone"], vehicle_id),
            )
            record_driver_change(
                connection,
                vehicle_id,
                row["id"],
                "CORRECT" if correcting else "ASSIGN",
                actor,
                current_assignment,
                row,
            )
            if self.media_layout:
                if (
                    current_assignment
                    and not correcting
                ):
                    self.media_layout.organize_driver(
                        connection,
                        current_assignment["id"],
                    )
                self.media_layout.organize_driver(
                    connection,
                    row["id"],
                )
            return row

    def end_driver(
        self,
        vehicle_id,
        assignment_id,
        ended_on,
        actor,
    ):
        with self._media_operation(), self.database.connect() as connection:
            if not connection.execute(
                "SELECT id FROM limo_vehicle WHERE id=%s AND NOT is_deleted FOR UPDATE",
                (vehicle_id,),
            ).fetchone():
                raise NotFound("Vehicle not found.")
            current_assignment = connection.execute(
                "SELECT * FROM hspace_driver_assignment WHERE vehicle_id=%s AND id=%s AND is_current FOR UPDATE",
                (vehicle_id, assignment_id),
            ).fetchone()
            if not current_assignment:
                raise DriverValidationError(
                    "last_worked_on",
                    "stalePeriod",
                    "This driver period is no longer current. Refresh the history.",
                )
            if (
                current_assignment["started_on"] is not None
                and ended_on <= current_assignment["started_on"]
            ):
                raise DriverValidationError(
                    "last_worked_on",
                    "endBeforeStart",
                    "The last working date cannot precede the start date.",
                )
            row = connection.execute(
                """

                    UPDATE hspace_driver_assignment
                    SET is_current=FALSE,ended_on=%s,updated_by=%s,updated_by_name=%s,updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s RETURNING *
                """,
                (ended_on, actor.id, actor.username, assignment_id),
            ).fetchone()
            connection.execute(
                "UPDATE limo_vehicle SET driver_name='',driver_phone='' WHERE id=%s",
                (vehicle_id,),
            )
            record_driver_change(
                connection,
                vehicle_id,
                assignment_id,
                "END",
                actor,
                current_assignment,
                row,
            )
            if self.media_layout:
                self.media_layout.organize_driver(
                    connection,
                    assignment_id,
                )
            return row

    def history(
        self,
        vehicle_id=None,
        query="",
        on_date=None,
    ):
        with self.database.connect() as connection:
            if (
                vehicle_id is not None
                and not connection.execute(
                    "SELECT 1 FROM limo_vehicle WHERE id=%s AND NOT is_deleted",
                    (vehicle_id,),
                ).fetchone()
            ):
                raise NotFound("Vehicle not found.")
            literal = (
                query.replace(
                    "!",
                    "!!",
                )
                .replace(
                    "%",
                    "!%",
                )
                .replace(
                    "_",
                    "!_",
                )
            )
            return connection.execute(
                """

                    SELECT a.*,
                           CASE WHEN a.started_on IS NULL
                                    OR a.ended_on>a.started_on THEN a.ended_on-1 ELSE NULL
                           END AS last_worked_on,v.plate_number,v.vehicle_type,

                      (SELECT count(*)
                       FROM limo_attachment f
                       WHERE f.driver_assignment_id=a.id
                         AND NOT f.is_deleted) AS attachment_count
                    FROM hspace_driver_assignment a
                    JOIN limo_vehicle v ON v.id=a.vehicle_id
                    WHERE NOT v.is_deleted
                      AND (%s::bigint IS NULL
                           OR a.vehicle_id=%s)
                      AND a.driver_name ILIKE %s ESCAPE '!'
                      AND (%s::date IS NULL
                           OR (a.started_on IS NOT NULL
                               AND a.started_on<=%s
                               AND (a.ended_on IS NULL
                                    OR %s<a.ended_on)))
                    ORDER BY a.vehicle_id,a.id DESC
                """,
                (vehicle_id, vehicle_id, "%" + literal + "%", on_date, on_date, on_date),
            ).fetchall()

    def corrections(
        self,
        vehicle_id,
    ):
        with self.database.connect() as connection:
            return connection.execute(
                """

                    SELECT c.action,c.actor_name,c.before_data,c.after_data,c.created_at
                    FROM hspace_driver_change c
                    JOIN limo_vehicle v ON v.id=c.vehicle_id
                    WHERE c.vehicle_id=%s
                      AND NOT v.is_deleted
                      AND c.action IN ('CORRECT','END')
                    ORDER BY c.id DESC
                """,
                (vehicle_id,),
            ).fetchall()
