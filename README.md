# H SPACE — Vehicle Management System

H SPACE is a local-first vehicle management website for a family car office. The backend uses **FastAPI on Uvicorn**, with PostgreSQL as its only runtime database. Cloud deployment is deferred while the application is tested locally.

The interface keeps the orange/charcoal identity, English by default, Arabic/RTL and light/dark mode. Vehicle cards open a detail view. Creating a vehicle requires its type and plate number; driver name, chassis number and manufacture year are optional text fields. Card photos are uploaded independently from gallery attachments.

## Current local installation

PostgreSQL 18 hosts the project-owned database `limousine_local`, with restricted role `limousine_local_app`. Private connection settings are in ignored `.env`. Existing vehicle rows, attachment metadata, cover records and file bytes were preserved during the framework conversion.

Four fixed account slots are configured: Adham qaneer, AbdAlhameed qaneer, Abdullah qaneer and Ahmad qaneer. Their existing passwords were retained. Private local credentials are in `.local/accounts.txt`, excluded from Git and Docker. Adham has the ADMIN role; the other three have MEMBER. All have the same vehicle access. Only the admin can disable, soft-delete or restore member accounts through Team. The admin account cannot be disabled or deleted through this feature. No public registration is provided.

From PowerShell in this directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -Command runserver
```

Open <http://127.0.0.1:8000/>. Stop with Ctrl+C. The server binds to loopback; use `-Port 8001` if needed. Restart after Python changes and use Ctrl+F5 after static asset changes. A physical phone cannot access this loopback address remotely without separate network configuration.

## Authentication and account data

Users have UUID identifiers, username, password hash, a constrained ADMIN/MEMBER role, active status, `is_deleted` and `deleted_at`. First/last name and email columns are absent. The application uses a Python role enumeration and PostgreSQL CHECK constraints, rather than a native PostgreSQL enum type.

Authentication uses opaque server-side sessions, **not access/refresh JWTs**. Sessions last 12 hours from sign-in without sliding renewal. Only the SHA-256 token hash is stored in PostgreSQL. The browser cookie is HttpOnly and SameSite=Lax; production enables Secure cookies. Sign-out, password changes, deactivation and soft deletion revoke sessions. Old framework sessions were discarded; sign in again after the conversion.

Signed session-bound CSRF tokens protect state changes, including login/logout. Passwords use PBKDF2-SHA256. New passwords require at least eight characters, cannot be entirely numeric and cannot match another account's password. There is no login rate limiter yet.

To change one account, supply its slot and username; the command prompts privately for the password:

```powershell
.\.runtime\python\python.exe manage.py setoperator 1 "Adham qaneer"
```

This does not update the private credentials note automatically.

## Files and previews

Uploads remain private in `media/vehicles/`; PostgreSQL stores filenames, storage keys, byte sizes and vehicle associations. Gallery uploads never choose or replace a card photo. Files are limited to 10 MiB, with bounded image/document validation. Images, PDF and TXT can be viewed through authenticated preview routes. DOCX/XLSX receive bounded local text/table previews; these do not reproduce Office formatting. Unsupported formats are rejected. No third-party viewer receives documents.

There is no vehicle/attachment deletion workflow, reservation system, accounting or maintenance workflow.

## Setup on a new machine

Use Python 3.12+ and PostgreSQL 14+. Dependencies are pinned in [requirements.txt](requirements.txt): FastAPI, Starlette, Pydantic, Uvicorn, Jinja2, python-multipart, psycopg, python-dotenv, Pillow and the HTTP test client. The frontend uses plain HTML/CSS/JavaScript and local assets, without npm or a build step.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe scripts/setup_local.py
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -Command runserver
```

Copy the example only when `.env` does not already exist. Setup privately prompts for the local PostgreSQL administrator password, provisions only the project database/role, writes application credentials locally, applies the schema and creates the four named accounts when none exist. Existing accounts are preserved. Never commit secrets or use this setup against another project's database.

Environment variables: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `HSPACE_SECRET_KEY`, `HSPACE_ALLOWED_HOSTS` and `HSPACE_ENV` (local or production). Production requires complete database settings, a strong secret and explicit allowed hosts. Private uploads, runtime, backups and generated artifacts are ignored.

## Database and architecture

In pgAdmin, refresh Databases, open **limousine_local → Schemas → public → Tables**. Right-click a table, then View/Edit Data → All Rows. The six application tables are:

| Table | Responsibility |
| --- | --- |
| limo_vehicle | Agreed vehicle text fields and creation time |
| limo_attachment | Gallery/file metadata |
| limo_vehicle_cover | Independent card photo metadata |
| hspace_user | Four UUID accounts, role and soft-delete status |
| hspace_session | Hashed session tokens and expiry |
| hspace_schema_migration | Applied schema versions |

```sql
SELECT id, plate_number, vehicle_type, driver_name,
       chassis_number, manufacture_year, created_at
FROM public.limo_vehicle ORDER BY id;
```

The conversion removed Django source, configuration, packages and old authentication/framework tables, including the temporary legacy schema. Core vehicle table names and identifiers were preserved. Ignored emergency backups under `.local/backups/` contain pre-conversion snapshots; they are not used by the running app. Backup restoration has not been tested. The current migration command initializes only the FastAPI schema and is idempotent; it is not an importer for older installations.

Responsibilities remain separated: business rules in domain, use cases/contracts in application, PostgreSQL/files/passwords/schema in infrastructure, and HTTP/templates/assets in presentation. `manage.py` is a small project CLI, not a framework dependency. It supports runserver, check, test, migrate, setoperator and a compatibility collectstatic command (no build is needed). Local schema changes are restricted to the configured loopback `limousine_local` database; do not run migrations against an unintended environment.

## Verification

```powershell
.\.runtime\python\python.exe manage.py check
.\.runtime\python\python.exe manage.py test
.\.runtime\python\python.exe scripts/check_readme.py
git diff --check
```

The conversion passed 48 isolated tests and compiled all four page templates. Real local PostgreSQL integration checks passed for all four existing passwords, UUID/roles, admin-only account changes, soft deletion/restoration, session revocation/expiry, CSRF, vehicle creation/editing, independent card photos, image/PDF/TXT/DOCX/XLSX previews and private downloads. Test fixtures were removed. Existing business rows, password hashes and attachment bytes were compared before/after and preserved. Removal of the legacy schema and an idempotent schema rerun were also verified. A fresh Uvicorn process returned HTTP 200 for live health, real PostgreSQL readiness and the branded login page after cleanup; the project interpreter could no longer import the removed framework. The verification server was stopped afterward. All four JavaScript files passed syntax checks.

The opt-in real database check is `python scripts/verify_local.py`. It requires the intended local database and current private credentials note. It temporarily changes a member's status and revokes sessions, then restores account status and removes its own records. Run it when other users are not working.

The test client currently emits an upstream deprecation warning about httpx; tests still pass. Browser appearance was checked on the previous UI version; the migrated backend has not yet received a fresh browser interaction check. Docker, backup restoration, device restart and deployment remain unverified.

CI runs the README change check, application/template check and isolated tests. It does not connect to the real local database. Documentation checking verifies that README changed, not that every statement is correct.

Docker/Compose supplies only the web service, binds its host port to loopback and uses a persistent media volume. A container needs separately configured PostgreSQL connectivity; its localhost is not the host computer. Production still needs HTTPS, rate limiting, operational hardening and tested database-plus-media backups.

## GitHub and local data

The repository contains application source, tests, documentation and setup examples. The README and supporting guides are maintained in English; the application's Arabic interface remains available.

Local connection secrets, account credentials, uploaded files, database backups, wallet files and the local Python runtime are excluded from Git. Cloning or pulling the repository does not restore the local database or attachments. Set up a private environment separately using the steps above. Pushing source to GitHub does not deploy the application or move local data to the cloud.

See [architecture](docs/architecture.md), [frontend](docs/frontend.md) and [remaining work](docs/next-steps.md).
