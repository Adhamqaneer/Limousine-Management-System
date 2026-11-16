#!/usr/bin/env python
"""Compatibility CLI for FastAPI development and local database management."""
import argparse
from getpass import getpass
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
    commands.add_parser("collectstatic")
    operator = commands.add_parser("setoperator")
    operator.add_argument("slot", type=int, choices=range(1, 5))
    operator.add_argument("username")
    args = parser.parse_args()
    if args.command == "runserver":
        import uvicorn
        host, port = args.address.rsplit(":", 1)
        if host not in ("127.0.0.1", "localhost", "::1"):
            parser.error("Development server must stay on loopback.")
        uvicorn.run("limousine.presentation.web.app:app", host=host, port=int(port), access_log=False)
    elif args.command == "test":
        import unittest
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT)))
        return 0 if result.wasSuccessful() else 1
    elif args.command == "check":
        from limousine.presentation.web.app import app
        for name in ("login.html", "home.html", "document_preview.html", "users.html"):
            from limousine.presentation.web.rendering import templates
            templates.get_template("web/" + name)
        print(f"FastAPI loaded; {len(app.routes)} routes and all templates checked.")
    elif args.command == "migrate":
        from limousine.config.runtime import load_settings
        from limousine.infrastructure.database import Database
        from limousine.infrastructure.migrations import migrate
        backup = migrate(Database(load_settings()))
        print("PostgreSQL migration completed. Existing vehicles/files preserved.")
        if backup:
            print("Pre-migration database backup saved under .local/backups/.")
    elif args.command == "collectstatic":
        print("FastAPI serves source static assets directly; no generated static build is required.")
    elif args.command == "cleanupfiles":
        from limousine.config.runtime import load_settings
        from limousine.infrastructure.database import Database
        from limousine.infrastructure.attachments import LocalAttachmentStore
        from limousine.infrastructure.file_cleanup import FileCleanup
        settings = load_settings()
        completed, pending = FileCleanup(Database(settings), LocalAttachmentStore(settings.media_root)).retry_pending()
        print(f"Cleanup batch: {completed} completed; {pending} deferred. Up to 100 entries per run.")
    elif args.command == "setoperator":
        from limousine.config.runtime import load_settings
        from limousine.infrastructure.database import Database
        from limousine.infrastructure.accounts import PostgresAccountRepository
        password = getpass("New password: ")
        if password != getpass("Confirm password: "):
            raise ValueError("Passwords do not match.")
        PostgresAccountRepository(Database(load_settings())).set_operator(args.slot, args.username, password)
        print("Account saved. Existing sessions revoked.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Command failed ({type(exc).__name__}). Check local settings; confidential details were suppressed.", file=sys.stderr)
        raise SystemExit(1)
