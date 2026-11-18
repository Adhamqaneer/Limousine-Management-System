"""PostgreSQL accounts and revocable opaque sessions; no JWT dependency."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from limousine.domain.accounts import Role, User, normalize_username, validate_slot
from limousine.domain.vehicles import NotFound
from limousine.infrastructure.passwords import hash_password, verify_password


def user_from_row(row):
    return User(
        row["id"],
        row["slot"],
        row["username"],
        Role(row["role"]),
        row["is_active"],
        row["is_deleted"],
        row["deleted_at"],
        row["created_at"],
        row["last_login"],
    )


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


class PostgresAccountRepository:
    def __init__(self, database):
        self.database = database

    def authenticate(self, username, password):
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM hspace_user WHERE username=%s", (username,)
            ).fetchone()
            # A dummy hash keeps missing users on the same expensive verification path.
            encoded = row["password_hash"] if row else "pbkdf2_sha256$1000000$dummy$invalid"
            matches = verify_password(password, encoded)
            return (
                user_from_row(row)
                if row and matches and row["is_active"] and not row["is_deleted"]
                else None
            )

    def list_users(self):
        with self.database.connect() as connection:
            return [
                user_from_row(row)
                for row in connection.execute("SELECT * FROM hspace_user ORDER BY slot").fetchall()
            ]

    def get_user(self, user_id):
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM hspace_user WHERE id=%s", (user_id,)).fetchone()
            if not row:
                raise NotFound("Account not found.")
            return user_from_row(row)

    def create_session(self, user_id, seconds):
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        with self.database.connect() as connection:
            connection.execute("DELETE FROM hspace_session WHERE expires_at <= CURRENT_TIMESTAMP")
            connection.execute(
                "INSERT INTO hspace_session (token_hash,user_id,expires_at) VALUES (%s,%s,%s)",
                (token_hash(token), user_id, expires),
            )
            connection.execute(
                "UPDATE hspace_user SET last_login=CURRENT_TIMESTAMP WHERE id=%s", (user_id,)
            )
        return token

    def session_user(self, token):
        if not token or len(token) > 128:
            return None
        with self.database.connect() as connection:
            row = connection.execute(
                """

                    SELECT u.*
                    FROM hspace_user u
                    JOIN hspace_session s ON s.user_id=u.id
                    WHERE s.token_hash=%s
                      AND s.expires_at>CURRENT_TIMESTAMP
                      AND u.is_active
                      AND NOT u.is_deleted
                """,
                (token_hash(token),),
            ).fetchone()
            return user_from_row(row) if row else None

    def delete_session(self, token):
        if token:
            with self.database.connect() as connection:
                connection.execute(
                    "DELETE FROM hspace_session WHERE token_hash=%s", (token_hash(token),)
                )

    def update_status(self, user_id, active, deleted):
        with self.database.connect() as connection:
            row = connection.execute(
                """

                    UPDATE hspace_user
                    SET is_active=%s,is_deleted=%s,deleted_at=CASE
                                                                  WHEN %s THEN COALESCE(deleted_at,
                                                                                 CURRENT_TIMESTAMP) ELSE NULL
                                                              END
                    WHERE id=%s
                      AND role<>'ADMIN' RETURNING *
                """,
                (active, deleted, deleted, user_id),
            ).fetchone()
            if not row:
                raise NotFound("Account not found or protected.")
            connection.execute("DELETE FROM hspace_session WHERE user_id=%s", (user_id,))
            return user_from_row(row)

    def set_operator(self, slot, username, password):
        validate_slot(slot)
        username = normalize_username(username)
        encoded = hash_password(password)
        with self.database.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(72730804)")
            for row in connection.execute("SELECT slot,password_hash FROM hspace_user").fetchall():
                if row["slot"] != slot and verify_password(password, row["password_hash"]):
                    raise ValueError("Each account must have a different password.")
            role = "ADMIN" if slot == 1 else "MEMBER"
            row = connection.execute(
                """

                    INSERT INTO hspace_user (id,
                                   slot, username, password_hash, role, is_active, is_deleted, created_at)
                    VALUES (%s,%s,%s,%s,%s,TRUE,FALSE,CURRENT_TIMESTAMP) ON CONFLICT (slot) DO
                    UPDATE
                    SET username=EXCLUDED.username,password_hash=EXCLUDED.password_hash RETURNING *
                """,
                (uuid4(), slot, username, encoded, role),
            ).fetchone()
            connection.execute("DELETE FROM hspace_session WHERE user_id=%s", (row["id"],))
            return user_from_row(row)
