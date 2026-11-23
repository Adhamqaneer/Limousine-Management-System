#!/usr/bin/env python
"""Local FastAPI development and PostgreSQL management commands."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    server = commands.add_parser("runserver")
    server.add_argument("address", nargs="?", default="127.0.0.1:8000")
    commands.add_parser("check")
    commands.add_parser("test")
    commands.add_parser("migrate")
    commands.add_parser("cleanupfiles")
    commands.add_parser("setpassword")
    args = parser.parse_args()
    if args.command == "runserver":
        import uvicorn

        host, port = args.address.rsplit(":", 1)
        if host not in ("127.0.0.1", "localhost", "::1"):
            parser.error("Development server must stay on loopback.")
        uvicorn.run(
            "limousine.presentation.web.app:app", host=host, port=int(port), access_log=False
        )
    elif args.command == "test":
        import unittest

        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
        )
        return 0 if result.wasSuccessful() else 1
    elif args.command == "check":
        from limousine.presentation.web.app import app

        for name in (
            "login.html",
            "home.html",
            "document_preview.html",
            "vehicle_report.html",
            "recycle_bin.html",
            "drivers.html",
            "office.html",
            "attachment_download.html",
        ):
            from limousine.presentation.web.rendering import templates

            templates.get_template("web/" + name)
        print(f"FastAPI loaded; {len(app.routes)} routes and all templates checked.")
    elif args.command == "migrate":
        from limousine.config.runtime import load_settings
        from limousine.infrastructure.database import Database
        from limousine.infrastructure.migrations import migrate, needs_operator_setup
        from limousine.infrastructure.passwords import prompt_password

        database = Database(load_settings())
        password = prompt_password() if needs_operator_setup(database) else None
        backup = migrate(database, operator_password=password)
        print("PostgreSQL migration completed. Existing vehicles/files preserved.")
        if backup:
            print("Pre-migration database backup saved under .local/backups/.")
    elif args.command == "cleanupfiles":
        from limousine.config.runtime import load_settings
        from limousine.infrastructure.attachments import LocalAttachmentStore
        from limousine.infrastructure.database import Database
        from limousine.infrastructure.file_cleanup import FileCleanup

        settings = load_settings()
        completed, pending = FileCleanup(
            Database(settings), LocalAttachmentStore(settings.media_root)
        ).retry_pending()
        print(
            f"Cleanup batch: {completed} completed; {pending} deferred. Up to 100 entries per run."
        )
    elif args.command == "setpassword":
        from limousine.config.runtime import load_settings
        from limousine.infrastructure.accounts import PostgresAccountRepository
        from limousine.infrastructure.database import Database
        from limousine.infrastructure.passwords import prompt_password

        PostgresAccountRepository(Database(load_settings())).set_password(prompt_password())
        print("Office password updated. Existing sessions revoked.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"Command failed ({type(exc).__name__}). Check local settings; confidential details were suppressed.",
            file=sys.stderr,
        )
        raise SystemExit(1)
