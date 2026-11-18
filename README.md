# H SPACE

A private vehicle-management website for a car office. It runs locally with FastAPI and PostgreSQL, in English or Arabic, with light and dark themes.

Four fixed accounts share vehicle records, owner details, driver periods and private photos/documents. Adham is ADMIN: only he can manage accounts, view deleted items/activity and restore records. Everyone can upload, rename and soft-delete files. Reports print selected vehicle fields or driver history, with optional office letterhead. Office files are separate from vehicle and driver documents.

## Requirements

- Python 3.12+ and PostgreSQL 14+, running locally.
- A current browser. Node.js 22+ is needed only for frontend tests.
- Python dependencies in [requirements.txt](requirements.txt).

## First setup

From the project folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/setup_local.py
```

Setup asks privately for the PostgreSQL administrator password. It creates the dedicated local database/role, writes `.env`, applies the schema and creates the four accounts. Initial credentials are saved in `.local/accounts.txt`. Keep both files private. Existing database settings/accounts are preserved; do not rerun setup to replace an existing installation.

This checkout already has `.env`; continue using it. Connection settings are `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT`. Setup also generates `HSPACE_SECRET_KEY`. The environment defaults to local.

## Run

```powershell
.\scripts\run.ps1
```

Open **http://127.0.0.1:8000/**. The launcher selects `.venv`, then the checkout's private `.runtime` Python, then system Python. Stop the server with **Ctrl+C** in its terminal. Closing the browser does not stop it.

Alternatively, use `python manage.py runserver` with the configured interpreter. Development stays on loopback. Refresh after UI updates; restart after Python changes.

## Checks

```powershell
.\scripts\run.ps1 check
.\scripts\run.ps1 test
node scripts/test_frontend.cjs
python scripts/check_readme.py
python scripts/check_database.py
```

Use your configured Python interpreter for the last two commands. The database audit is read-only and requires the intended local `limousine_local` settings. Python tests use isolated repositories/temp files; frontend tests need no npm installation. CI runs code/template, Python, frontend and README checks.

Previous refactoring checks (before the media-folder change) passed: 101 Python tests, 11 frontend harness files, 17 browser-script syntax checks, all eight templates/49 routes and the read-only PostgreSQL audit. Native browser checks and Docker execution remain unverified.

Navigation follow-up: active links keep separate `nav-link` and `active` CSS classes after template formatting. Eight focused navigation/report/asset tests passed, covering the active state on all six destinations.

## Data and maintenance

PostgreSQL stores records and file metadata. Private originals are organized under `media/`:

```text
media/
  office/photos/ and office/files/
  vehicles/vehicle-<id>/photos/, files/ and covers/
  drivers/<name> -- <start> to <last-working-day> --period-<id>/photos/ and files/
```

Driver folder labels use Arabic text, ISO dates with the year, and "now" while current. Ending/replacing a driver or correcting name/start dates updates the folder and all associated storage keys, including deleted originals. Unknown starts stay labeled unknown. A short period ID prevents name/date collisions. Deletion still retains bytes for administrator recovery.

Schema 9 permits these paths. The existing local originals were reorganized after private database/media backups under `.local/backups/`. New uploads follow the same structure. Restart the server for the new handlers. No automated tests or browser checks were run for this change at the owner's request. Back up **both PostgreSQL and media**, plus private configuration. A Git checkout/push does not include local data or credentials.

- Apply a documented schema update: `python manage.py migrate`. Existing installations receive a private database backup first. The folder organization uses schema 9.
- Change a fixed account name/password: `python manage.py setoperator <slot> "<username>"` (slots 1-4). Enter the password privately; existing sessions are revoked.
- Retry failed-upload cleanup: `python manage.py cleanupfiles`. Referenced files, including deleted ones, are retained.
- Optional Docker files are retained for a future decision. They are not needed locally and were not built/tested in this review.

## Understand the code

Start with [architecture and database](docs/architecture.md), then [frontend](docs/frontend.md). [Maintenance](docs/maintenance.md) covers deeper checks; [remaining work](docs/next-steps.md) records open decisions and limitations.

Native browser/mobile/printing checks and a backup-restore drill remain outstanding. Server/desktop packaging is undecided; this is not a production-readiness claim.
