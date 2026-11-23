"""PostgreSQL sign-in for the office account and revocable opaque sessions."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from limousine.domain.accounts import OPERATOR_USERNAME, User
from limousine.infrastructure.passwords import hash_password, verify_password


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


class PostgresAccountRepository:
    def __init__(self, database):
        self.database = database

    def sign_in(self, username, password, seconds, previous_token=""):
        with self.database.connect() as connection:
            # Hold the credential stable until the session is created.
            row = connection.execute(
                "SELECT user_id,password_hash FROM hspace_operator FOR SHARE"
            ).fetchone()
            encoded = row["password_hash"] if row else "pbkdf2_sha256$1000000$dummy$invalid"
            if (
                not verify_password(password, encoded)
                or not row
                or username != OPERATOR_USERNAME
            ):
                return None
            token = secrets.token_urlsafe(32)
            expires = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            connection.execute(
                "DELETE FROM hspace_session WHERE expires_at <= CURRENT_TIMESTAMP OR token_hash=%s",
                (token_hash(previous_token),),
            )
            connection.execute(
                "INSERT INTO hspace_session (token_hash,user_id,expires_at) VALUES (%s,%s,%s)",
                (token_hash(token), row["user_id"], expires),
            )
            connection.execute(
                "UPDATE hspace_user SET last_login=CURRENT_TIMESTAMP WHERE id=%s",
                (row["user_id"],),
            )
            return token

    def operator(self):
        with self.database.connect() as connection:
            row = connection.execute("SELECT user_id FROM hspace_operator").fetchone()
            if not row:
                raise ValueError("Set up the office account first.")
            return User(row["user_id"], OPERATOR_USERNAME)

    def session_user(self, token):
        if not token or len(token) > 128:
            return None
        with self.database.connect() as connection:
            row = connection.execute(
                """SELECT s.user_id FROM hspace_session s
                   JOIN hspace_operator o ON o.user_id=s.user_id
                   WHERE s.token_hash=%s AND s.expires_at>CURRENT_TIMESTAMP""",
                (token_hash(token),),
            ).fetchone()
            return User(row["user_id"], OPERATOR_USERNAME) if row else None

    def delete_session(self, token):
        if token:
            with self.database.connect() as connection:
                connection.execute(
                    "DELETE FROM hspace_session WHERE token_hash=%s", (token_hash(token),)
                )

    def set_password(self, password):
        encoded = hash_password(password)
        with self.database.connect() as connection:
            updated = connection.execute(
                "UPDATE hspace_operator SET password_hash=%s", (encoded,)
            )
            if updated.rowcount != 1:
                raise ValueError("Set up the office account first.")
            connection.execute("DELETE FROM hspace_session")
