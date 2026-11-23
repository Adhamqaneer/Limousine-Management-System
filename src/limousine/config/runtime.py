"""Runtime settings for the local-first FastAPI application."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""
    db_host: str = "127.0.0.1"
    db_port: str = "5432"
    secret: str = "local-development-only-hspace"
    production: bool = False
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost", "testserver")
    media_root: Path = ROOT / "media"
    session_seconds: int = 12 * 60 * 60
    backup_directory: Path = ROOT / ".local" / "backups"
    pg_dump_path: Path | None = None

    @property
    def database_configured(self):
        return bool(self.db_name and self.db_user and self.db_password)

    def validate(self):
        values = (self.db_name, self.db_user, self.db_password)
        if any(values) and not all(values):
            raise ValueError("Complete DB_NAME, DB_USER and DB_PASSWORD together.")
        if self.production and (
            not self.database_configured
            or len(self.secret) < 50
            or not self.allowed_hosts
            or "*" in self.allowed_hosts
        ):
            raise ValueError(
                "Production requires PostgreSQL, a strong HSPACE_SECRET_KEY and explicit allowed hosts."
            )
        return self


def load_settings():
    load_dotenv(ROOT / ".env", override=False)
    production = os.getenv("HSPACE_ENV", "local") == "production"
    return Settings(
        db_name=os.getenv("DB_NAME", "").strip(),
        db_user=os.getenv("DB_USER", "").strip(),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=os.getenv("DB_PORT", "5432"),
        secret=os.getenv("HSPACE_SECRET_KEY") or "local-development-only-hspace",
        production=production,
        allowed_hosts=tuple(
            value.strip()
            for value in os.getenv("HSPACE_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(
                ","
            )
            if value.strip()
        ),
    ).validate()
