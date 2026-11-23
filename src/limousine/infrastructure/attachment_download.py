"""Read one consistent selection of active vehicle-gallery originals."""

from limousine.domain.vehicles import DomainError, NotFound


class PostgresAttachmentDownloadRepository:
    def __init__(
        self,
        database,
    ):
        self.database = database

    def selection(
        self,
        vehicle_ids,
        category_ids,
    ):
        with self.database.connect() as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            vehicles, categories = self._scope(
                connection,
                vehicle_ids,
                category_ids,
            )
            files = connection.execute(
                """SELECT f.*,v.plate_number FROM limo_attachment f JOIN limo_vehicle v ON v.id=f.vehicle_id
                WHERE f.vehicle_id=ANY(%s) AND f.category_id=ANY(%s) AND f.driver_assignment_id IS NULL
                  AND NOT f.is_deleted AND NOT v.is_deleted
                ORDER BY f.vehicle_id,f.category_id,f.id LIMIT 1001""",
                (vehicle_ids, category_ids),
            ).fetchall()
            return vehicles, categories, files

    def availability(
        self,
        vehicle_ids,
        category_ids,
    ):
        with self.database.connect() as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            vehicles, categories = self._scope(
                connection,
                vehicle_ids,
                category_ids,
            )
            counts = connection.execute(
                """SELECT f.vehicle_id,f.category_id,count(*) AS count
                FROM limo_attachment f JOIN limo_vehicle v ON v.id=f.vehicle_id
                WHERE f.vehicle_id=ANY(%s) AND f.category_id=ANY(%s) AND f.driver_assignment_id IS NULL
                  AND NOT f.is_deleted AND NOT v.is_deleted
                GROUP BY f.vehicle_id,f.category_id""",
                (vehicle_ids, category_ids),
            ).fetchall()
            return vehicles, categories, counts

    @staticmethod
    def _scope(
        connection,
        vehicle_ids,
        category_ids,
    ):
        vehicles = connection.execute(
            "SELECT id,plate_number FROM limo_vehicle WHERE id=ANY(%s) AND NOT is_deleted ORDER BY id",
            (vehicle_ids,),
        ).fetchall()
        if len(vehicles) != len(vehicle_ids):
            raise NotFound("A selected vehicle is no longer available.")
        categories = connection.execute(
            "SELECT id,name FROM hspace_attachment_category WHERE id=ANY(%s) AND merged_into IS NULL",
            (category_ids,),
        ).fetchall()
        if len(categories) != len(category_ids):
            raise DomainError("A selected category changed. Refresh before downloading.")
        return vehicles, categories
