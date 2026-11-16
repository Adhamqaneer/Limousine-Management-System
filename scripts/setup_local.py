"""Provision only this project's local PostgreSQL database; never print secrets.

Use the installed PostgreSQL administrator password via getpass, an existing
ignored .env setup field, or --password-stdin (for a hidden terminal session).
Creates a dedicated restricted database role; existing roles/data are preserved.
"""

import argparse
from getpass import getpass
from pathlib import Path
import secrets
import sys

import psycopg
from psycopg import sql
from dotenv import dotenv_values, set_key, unset_key

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--password-stdin", action="store_true")
    args = parser.parse_args()
    env_path = ROOT / ".env"
    values = dotenv_values(env_path)
    if values.get("DB_HOST", "127.0.0.1") not in ("127.0.0.1", "localhost", "::1"):
        print("Local setup requires a loopback PostgreSQL host.")
        return 1
    # Keep setup scoped to unique project-owned names, never an unrelated DB.
    database, role = "limousine_local", "limousine_local_app"
    existing = values.get("DB_NAME")
    if existing and existing != database:
        print("Existing database settings were preserved. Configure this database manually.")
        return 1
    if args.password_stdin:
        # Suppress terminal echo before signalling readiness for the secret.
        if sys.platform == "win32":
            import ctypes
            kernel = ctypes.windll.kernel32
            handle = kernel.GetStdHandle(-10)
            previous = ctypes.c_ulong()
            if not kernel.GetConsoleMode(handle, ctypes.byref(previous)):
                print("A private terminal is required.")
                return 1
            kernel.SetConsoleMode(handle, previous.value & ~4)
        else:
            import termios
            previous = termios.tcgetattr(sys.stdin)
            mode = termios.tcgetattr(sys.stdin)
            mode[3] &= ~termios.ECHO
            termios.tcsetattr(sys.stdin, termios.TCSANOW, mode)
        print("Ready for PostgreSQL password (input is hidden).", flush=True)
        try:
            admin_password = sys.stdin.readline().rstrip("\r\n")
        finally:
            if sys.platform == "win32":
                kernel.SetConsoleMode(handle, previous.value)
            else:
                termios.tcsetattr(sys.stdin, termios.TCSANOW, previous)
    else:
        admin_password = values.get("LOCAL_POSTGRES_ADMIN_PASSWORD") or getpass("PostgreSQL postgres password: ")
    application_password = values.get("DB_PASSWORD") or secrets.token_urlsafe(32)
    stage = "administrator connection"
    try:
        with psycopg.connect(dbname="postgres", user="postgres", password=admin_password,
                             host="127.0.0.1", port=values.get("DB_PORT") or "5432",
                             connect_timeout=5, autocommit=True) as conn:
            stage = "project role and database"
            role_exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone()
            if role_exists and not (values.get("DB_USER") == role and values.get("DB_PASSWORD")):
                print("The project role already exists. Restore its .env credentials; no password was changed.")
                return 1
            if not role_exists:
                conn.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE").format(
                    sql.Identifier(role), sql.Literal(application_password)))
            db_owner = conn.execute("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = %s", (database,)).fetchone()
            if db_owner and db_owner[0] != role:
                print("Database name belongs to another owner. No existing data was changed.")
                return 1
            if not db_owner:
                conn.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(database), sql.Identifier(role)))
        stage = "local settings"
        for key, value in {"DB_HOST": "127.0.0.1", "DB_PORT": values.get("DB_PORT") or "5432",
                           "DB_NAME": database, "DB_USER": role, "DB_PASSWORD": application_password}.items():
            set_key(env_path, key, value)
        if not values.get("HSPACE_SECRET_KEY"):
            set_key(env_path, "HSPACE_SECRET_KEY", secrets.token_urlsafe(64))
        unset_key(env_path, "LOCAL_POSTGRES_ADMIN_PASSWORD") if "LOCAL_POSTGRES_ADMIN_PASSWORD" in values else None
        sys.path.insert(0, str(ROOT / "src"))
        from limousine.config.runtime import load_settings
        from limousine.infrastructure.database import Database
        from limousine.infrastructure.migrations import migrate
        from limousine.infrastructure.accounts import PostgresAccountRepository
        stage = "database migration"
        database_adapter = Database(load_settings())
        migrate(database_adapter)
        accounts = PostgresAccountRepository(database_adapter)
        existing_users = accounts.list_users()
        if not existing_users:
            directory = ROOT / ".local"
            directory.mkdir(exist_ok=True)
            access_file = directory / "accounts.txt"
            if access_file.exists():
                print("An accounts file already exists; configure accounts using setoperator.")
                return 1
            names = ["Adham qaneer", "AbdAlhameed qaneer", "Abdullah qaneer", "Ahmad qaneer"]
            with access_file.open("x", encoding="utf-8") as output:
                access_file.chmod(0o600)
                output.write("Local accounts - keep private. Change with: manage.py setoperator <slot> <username>\n")
                for slot, username in enumerate(names, 1):
                    password = secrets.token_urlsafe(6)
                    accounts.set_operator(slot, username, password)
                    output.write(f"{username}: {password}\n")
                    output.flush()
        print("Local database, migrations and four accounts are ready.")
        print("Account credentials are in .local/accounts.txt (ignored by Git).")
        return 0
    except Exception as error:
        # Database exceptions may include server or SQL details. Do not emit them.
        reason = ""
        if isinstance(error, psycopg.OperationalError):
            detail = str(error).lower()
            if "password authentication failed" in detail:
                reason = " PostgreSQL rejected the administrator password."
            elif "refused" in detail:
                reason = " PostgreSQL refused the connection."
            elif "timeout" in detail:
                reason = " The connection timed out."
        print(f"Local setup did not finish at {stage} ({type(error).__name__}).{reason}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
