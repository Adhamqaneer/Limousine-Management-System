"""PostgreSQL implementation of the framework-independent vehicle contract."""
from psycopg import sql
from limousine.domain.vehicles import Attachment, NotFound, Vehicle, VehicleCover

def attachment(row):
    return Attachment(row["id"], row["vehicle_id"], row["storage_key"], row["original_name"],
                      row["kind"], row["size"], row["created_at"])

class PostgresVehicleRepository:
    def __init__(self, database):
        self.database = database

    def _vehicle(self, connection, row):
        attachments = connection.execute("SELECT * FROM limo_attachment WHERE vehicle_id=%s ORDER BY id", (row["id"],)).fetchall()
        photo = connection.execute("SELECT * FROM limo_vehicle_cover WHERE vehicle_id=%s", (row["id"],)).fetchone()
        return self._build_vehicle(row, attachments, photo)

    @staticmethod
    def _build_vehicle(row, attachments, photo):
        return Vehicle(
            row["id"], row["plate_number"], row["created_at"], tuple(attachment(item) for item in attachments),
            row["vehicle_type"], row["driver_name"], row["chassis_number"], row["manufacture_year"],
            VehicleCover(row["id"], photo["storage_key"], photo["original_name"], photo["size"]) if photo else None,
        )

    def list_vehicles(self):
        with self.database.connect() as connection:
            rows = connection.execute("SELECT * FROM limo_vehicle ORDER BY id").fetchall()
            if not rows:
                return []
            ids = [row["id"] for row in rows]
            attachments = {vehicle_id: [] for vehicle_id in ids}
            for item in connection.execute("SELECT * FROM limo_attachment WHERE vehicle_id=ANY(%s) ORDER BY id", (ids,)).fetchall():
                attachments[item["vehicle_id"]].append(item)
            covers = {item["vehicle_id"]: item for item in connection.execute("SELECT * FROM limo_vehicle_cover WHERE vehicle_id=ANY(%s)", (ids,)).fetchall()}
            return [self._build_vehicle(row, attachments[row["id"]], covers.get(row["id"])) for row in rows]

    def get_vehicle(self, vehicle_id):
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM limo_vehicle WHERE id=%s", (vehicle_id,)).fetchone()
            if not row:
                raise NotFound("Vehicle not found.")
            return self._vehicle(connection, row)

    def create_vehicle(self, plate_number, **fields):
        values = {"plate_number": plate_number, "vehicle_type": "", "driver_name": "", "chassis_number": "", "manufacture_year": "", **fields}
        with self.database.connect() as connection:
            query = sql.SQL("INSERT INTO limo_vehicle ({},created_at) VALUES ({},CURRENT_TIMESTAMP) RETURNING *").format(
                sql.SQL(",").join(map(sql.Identifier, values)), sql.SQL(",").join(sql.Placeholder() for _ in values))
            return self._vehicle(connection, connection.execute(query, tuple(values.values())).fetchone())

    def update_vehicle(self, vehicle_id, **fields):
        with self.database.connect() as connection:
            query = sql.SQL("UPDATE limo_vehicle SET {} WHERE id=%s RETURNING id").format(
                sql.SQL(",").join(sql.SQL("{}=%s").format(sql.Identifier(name)) for name in fields))
            if not connection.execute(query, (*fields.values(), vehicle_id)).fetchone():
                raise NotFound("Vehicle not found.")
        return self.get_vehicle(vehicle_id)

    def add_attachment(self, vehicle_id, **metadata):
        with self.database.connect() as connection:
            row = connection.execute(
                "INSERT INTO limo_attachment (vehicle_id,storage_key,original_name,kind,size,created_at) VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP) RETURNING *",
                (vehicle_id, metadata["storage_key"], metadata["original_name"], metadata["kind"], metadata["size"]),
            ).fetchone()
            return attachment(row)

    def get_attachment(self, vehicle_id, attachment_id):
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM limo_attachment WHERE vehicle_id=%s AND id=%s", (vehicle_id, attachment_id)).fetchone()
            if not row:
                raise NotFound("Attachment not found.")
            return attachment(row)

    def replace_cover(self, cover):
        with self.database.connect() as connection:
            if not connection.execute("SELECT id FROM limo_vehicle WHERE id=%s FOR UPDATE", (cover.vehicle_id,)).fetchone():
                raise NotFound("Vehicle not found.")
            old = connection.execute("SELECT storage_key FROM limo_vehicle_cover WHERE vehicle_id=%s", (cover.vehicle_id,)).fetchone()
            connection.execute(
                "INSERT INTO limo_vehicle_cover (vehicle_id,storage_key,original_name,size) VALUES (%s,%s,%s,%s) ON CONFLICT (vehicle_id) DO UPDATE SET storage_key=EXCLUDED.storage_key,original_name=EXCLUDED.original_name,size=EXCLUDED.size",
                (cover.vehicle_id, cover.storage_key, cover.original_name, cover.size))
            if old and old["storage_key"] != cover.storage_key:
                self._queue_cleanup(connection, old["storage_key"])
            return cover, old["storage_key"] if old else None

    @staticmethod
    def _queue_cleanup(connection, key):
        connection.execute("INSERT INTO hspace_file_cleanup(storage_key) VALUES (%s) ON CONFLICT DO NOTHING", (key,))

    def delete_attachment(self, vehicle_id, attachment_id):
        with self.database.connect() as connection:
            row = connection.execute(
                "DELETE FROM limo_attachment WHERE vehicle_id=%s AND id=%s RETURNING storage_key",
                (vehicle_id, attachment_id)).fetchone()
            if not row:
                raise NotFound("Attachment not found for this vehicle.")
            self._queue_cleanup(connection, row["storage_key"])
            return row["storage_key"]

    def delete_cover(self, vehicle_id):
        with self.database.connect() as connection:
            # Serialize removal with replacement, including the no-cover case.
            if not connection.execute("SELECT id FROM limo_vehicle WHERE id=%s FOR UPDATE", (vehicle_id,)).fetchone():
                raise NotFound("Vehicle not found.")
            row = connection.execute("DELETE FROM limo_vehicle_cover WHERE vehicle_id=%s RETURNING storage_key", (vehicle_id,)).fetchone()
            if not row:
                raise NotFound("This vehicle has no card photo.")
            self._queue_cleanup(connection, row["storage_key"])
            return row["storage_key"]
