"""Own the loopback PostgreSQL instance for this Windows desktop profile."""

import json
import os
import secrets
import socket
import subprocess
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
from psycopg import sql

from limousine.config.runtime import Settings

HOST = "127.0.0.1"
DATABASE_NAME = "limousine_local"
ADMIN_ROLE = "hspace_local_admin"
APP_ROLE = "limousine_local_app"


def loopback_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return listener.getsockname()[1]


class DesktopPostgres:
    def __init__(self, binaries, profile):
        self.binaries = binaries
        self.profile = profile
        self.data = profile / "postgres-data"
        self.credentials = profile / "desktop-settings.json"

    def _run(self, program, *arguments):
        # Inherited PostgreSQL settings may point at another installation.
        environment = {key: value for key, value in os.environ.items() if not key.startswith("PG")}
        return subprocess.run(
            [str(self.binaries / f"{program}.exe"), *map(str, arguments)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
            timeout=100,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).returncode

    def _credentials(self):
        if self.credentials.is_file():
            return json.loads(self.credentials.read_text(encoding="utf-8"))
        if self.data.exists():
            raise RuntimeError("The desktop database settings are missing. Restore the profile backup.")

        credentials = {
            "admin_password": secrets.token_urlsafe(32),
            "database_password": secrets.token_urlsafe(32),
            "session_secret": secrets.token_urlsafe(64),
        }
        temporary = self.credentials.with_suffix(".tmp")
        temporary.write_text(json.dumps(credentials), encoding="utf-8")
        temporary.replace(self.credentials)
        return credentials

    def _initialize(self, admin_password):
        if self.data.exists():
            if not (self.data / "PG_VERSION").is_file():
                raise RuntimeError("The desktop PostgreSQL data folder is incomplete.")
            return

        with TemporaryDirectory(prefix="pg-init-", dir=self.profile) as staging:
            temporary = Path(staging)
            password_file = temporary / "password"
            password_file.write_text(admin_password + "\n", encoding="ascii")
            cluster = temporary / "cluster"
            try:
                status = self._run(
                    "initdb",
                    "--pgdata", cluster,
                    "--username", ADMIN_ROLE,
                    "--pwfile", password_file,
                    "--auth", "scram-sha-256",
                    "--encoding", "UTF8",
                    "--locale", "C",
                )
            finally:
                password_file.unlink(missing_ok=True)
            if status != 0:
                raise RuntimeError("Could not initialize the private PostgreSQL instance.")
            cluster.rename(self.data)

    def _provision_database(self, port, credentials):
        with psycopg.connect(
            host=HOST,
            port=port,
            dbname="postgres",
            user=ADMIN_ROLE,
            password=credentials["admin_password"],
            autocommit=True,
            connect_timeout=5,
        ) as connection:
            if not connection.execute(
                "SELECT 1 FROM pg_roles WHERE rolname=%s", (APP_ROLE,)
            ).fetchone():
                connection.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE")
                    .format(sql.Identifier(APP_ROLE), sql.Literal(credentials["database_password"]))
                )
            if not connection.execute(
                "SELECT 1 FROM pg_database WHERE datname=%s", (DATABASE_NAME,)
            ).fetchone():
                connection.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}")
                    .format(sql.Identifier(DATABASE_NAME), sql.Identifier(APP_ROLE))
                )

    @contextmanager
    def running(self):
        credentials = self._credentials()
        self._initialize(credentials["admin_password"])
        status = self._run("pg_ctl", "status", "-D", self.data)
        if status == 0:
            # Release an instance from a previous abnormal application exit.
            self._stop()
        elif status != 3:
            raise RuntimeError("Could not check the private PostgreSQL instance.")

        port = loopback_port()
        options = f"-h {HOST} -p {port} -c log_min_error_statement=panic"
        try:
            status = self._run(
                "pg_ctl", "start", "-D", self.data, "-o", options, "-w", "-t", "45",
                "-l", self.profile / "postgres.log",
            )
            if status != 0:
                raise RuntimeError("Could not start the private PostgreSQL instance.")
            self._provision_database(port, credentials)

            yield Settings(
                db_name=DATABASE_NAME,
                db_user=APP_ROLE,
                db_password=credentials["database_password"],
                db_host=HOST,
                db_port=str(port),
                secret=credentials["session_secret"],
                allowed_hosts=(HOST,),
                media_root=self.profile / "media",
                backup_directory=self.profile / "backups",
                pg_dump_path=self.binaries / "pg_dump.exe",
            )
        finally:
            if self._run("pg_ctl", "status", "-D", self.data) == 0:
                self._stop()

    def _stop(self):
        if self._run("pg_ctl", "stop", "-D", self.data, "-m", "fast", "-w", "-t", "45") != 0:
            raise RuntimeError("Could not stop the private PostgreSQL instance.")
