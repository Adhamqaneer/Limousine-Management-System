"""Back up and arrange existing local originals into office/vehicle/driver folders."""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from limousine.config.runtime import load_settings
    from limousine.infrastructure.attachments import LocalAttachmentStore
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.media_layout import MediaOrganizer
    from limousine.infrastructure.migrations import backup_database, migrate

    settings = load_settings()
    if settings.db_name != "limousine_local" or settings.db_host not in (
        "127.0.0.1",
        "localhost",
        "::1",
    ):
        raise ValueError("Media organization requires the intended local database.")
    database = Database(settings)
    backup = migrate(database)
    if backup is None:
        backup_database(settings)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    media_backup = ROOT / ".local/backups" / ("media-before-organization-" + stamp)
    if settings.media_root.exists():
        shutil.make_archive(str(media_backup), "zip", settings.media_root)
    organizer = MediaOrganizer(database, LocalAttachmentStore(settings.media_root))
    organizer.organize_all()
    print("Media organized. Database/media backups are under .local/backups/.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"Media organization stopped ({type(error).__name__}); originals and backups retained.",
            file=sys.stderr,
        )
        raise SystemExit(1)
