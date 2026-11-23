# H SPACE

A private vehicle-management website for a car office. It runs locally with FastAPI and PostgreSQL, in English or Arabic, with light and dark themes.

Sign in with the office account, **H space**, to manage vehicle records, driver periods, private photos and documents, and to view activity or restore deleted items. Reports print selected vehicle fields or driver history, with optional office letterhead. Office files are separate from vehicle and driver documents.

On **Print vehicle data**, select fields in the order you want them to appear in the preview, on paper or in the PDF.

On **Office files**, add photos or files directly and download each section as a ZIP.

Vehicle, office and driver attachment lists show their first three rows before scrolling internally. Other long lists also scroll within their sections. Report previews scroll on screen and print all rows.

When adding a vehicle, use Arabic or English letters and spaces for its type. A new or changed vehicle number requires English digits with at least one hyphen between digit groups, such as `50-31142`. A number assigned to another record cannot be used, including while that record is in Deleted items.

## Download attachments by type

Add photos or files to a vehicle, then click the category beside an uploaded attachment to classify it. Vehicle uploads start as Other. Vehicle license, Direction card and Customs declaration are available by default. A named type permits one active attachment per vehicle across Photos and Files. Other permits multiple. In the category dialog, choose Other and enter a new type name to add a permanent shared choice. Other stays last.

On Vehicles, click **Download attachments**, select the document types, review the per-vehicle Available/Missing table, then click **Download ZIP**. The current search/filters apply; without filters this includes all vehicles. Each vehicle has a folder named by its plate, containing the original files in every supported format. Missing document types are listed in _missing-documents.txt inside the ZIP. Existing vehicle-data and driver-history printing is unchanged.

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

Setup asks privately for the PostgreSQL administrator password and the password for **H space**. It creates the dedicated local database and role, writes `.env` and applies the schema. The office password is stored as a hash in PostgreSQL.

This checkout already has `.env`; continue using it. Connection settings are `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT`. Setup also generates `HSPACE_SECRET_KEY`. The environment defaults to local.

## Upgrade an existing installation

Stop the local server and run `python manage.py migrate` with the project's configured interpreter. Enter and confirm the password for **H space** when prompted. Schema 12 backs up the existing database first, revokes old sessions and retires the former sign-ins. Existing records, files and the names on past activity entries are retained. Restart the server and sign in as **H space**.

## Run

```powershell
.\scripts\run.ps1
```

Open **http://127.0.0.1:8000/**. The launcher selects `.venv`, then the checkout's private `.runtime` Python, then system Python. Stop the server with **Ctrl+C** in its terminal. Closing the browser does not stop it.

Alternatively, use `python manage.py runserver` with the configured interpreter. Development stays on loopback. Refresh after UI updates; restart after Python changes.

## Windows desktop preview

Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_desktop.ps1` on this development computer. On a fresh checkout, install `requirements-desktop.txt` in the configured Python environment first. The preview requires WebView2 and PostgreSQL binaries. Pass `-PostgresBin` if PostgreSQL is in a different location.

H SPACE opens in its own window with the office logo as its Windows icon. On first launch, choose a password for `H space` and sign in. The preview starts with empty records and saves changes under `.local/desktop-preview/` in this checkout. See [desktop preview](docs/desktop.md) for details.

## Checks

```powershell
.\scripts\run.ps1 check
.\scripts\run.ps1 test
node scripts/test_frontend.cjs
python scripts/check_readme.py
python scripts/check_database.py
```

Use your configured Python interpreter for the last two commands. The database audit is read-only and requires the intended local `limousine_local` settings. Python tests use isolated repositories/temp files; frontend tests need no npm installation. CI runs code/template, Python, frontend and README checks. Known static design-detector limitations are documented in [maintenance](docs/maintenance.md).

## Data and maintenance

PostgreSQL stores records and file metadata. Vehicle, driver and office uploads allow up to 25 MB per file, including card photos. Photos also have a 40-megapixel limit. Private originals are organized under `media/`:

```text
media/
  office/photos/ and office/files/
  vehicles/vehicle-<id>/photos/, files/ and covers/
  drivers/<name> -- <start> to <last-working-day> --period-<id>/photos/ and files/
```

Driver folder labels use Arabic text, ISO dates with the year, and "now" while current. Ending/replacing a driver or correcting name/start dates updates the folder and all associated storage keys, including deleted originals. Unknown starts stay labeled unknown. A short period ID prevents name/date collisions. Deletion retains the originals for recovery.

Schema 9 introduced these paths; schema 10 adds attachment categories. The existing local originals were reorganized after private database/media backups under `.local/backups/`. New uploads follow the same structure. Restart the server for the new handlers. No automated tests or browser checks were run for this change at the owner's request. Back up **both PostgreSQL and media**, plus private configuration. A Git checkout/push does not include local data or credentials.

- Apply a documented schema update with `python manage.py migrate`. The current schema is 14. The desktop preview applies the update on startup after backing up the database.
- Change the office password with `python manage.py setpassword`. This revokes existing sessions.
- Retry failed-upload cleanup: `python manage.py cleanupfiles`. Referenced files, including deleted ones, are retained.

## Understand the code

Start with [architecture and database](docs/architecture.md), then [frontend](docs/frontend.md). [Maintenance](docs/maintenance.md) covers deeper checks; [remaining work](docs/next-steps.md) records open decisions and limitations.

For Python and JavaScript, put each parameter or argument on its own line when a function or call takes more than one. Use separate lines for compound conditions and blocks for JavaScript conditionals. See [maintenance](docs/maintenance.md) for formatting and cleanup details.

See maintenance docs for category/download verification results. Restart the server after this update.

Native browser/mobile/printing checks and a backup-restore drill remain outstanding. Distribution packaging is deferred.
