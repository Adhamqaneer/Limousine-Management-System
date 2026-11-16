# H SPACE — Vehicle Management System

H SPACE is a local-first vehicle management website for a family car office. The backend uses **FastAPI on Uvicorn**, with PostgreSQL as its only runtime database. Cloud deployment is deferred while the application is tested locally.

The interface keeps the orange/charcoal identity, English by default, Arabic/RTL and light/dark mode. Vehicle cards open a detail view. Creating a vehicle requires its type and plate number; driver name, chassis number and manufacture year are optional text fields. Card photos are uploaded independently from gallery attachments.

## Interface and backgrounds

The H SPACE Studio refresh uses the owner's orange/charcoal logo identity and a locally generated **Toyota Camry** architectural background. Sign-in has a cinematic full-scene backdrop and an opaque, readable form; the vehicle list has a matching hero, with a calmer ambient background throughout the workspace. The image is decorative and is never assigned as a vehicle's uploaded card photo.

Navigation, cards, forms, Team and Office-document previews share the new visual system. English/Arabic RTL and both themes remain available on all pages; light mode uses warm-white data surfaces and a white sign-in panel against the cinematic scene. Sign-in includes a Show/Hide password control without changing authentication. Team provides retry feedback when loading fails.

The refresh changes presentation only: no database migration, new environment setting or dependency is required. The previous deletion feature still requires schema version 2. Existing data, attachments, account roles and APIs are unchanged. The public background asset is `static/web/hspace-camry-studio.png` (1672 × 941, approximately 1.7 MiB), generated for this project with imagegen and served locally. Shared header/icons and seven small browser scripts support the pages; there are no external fonts, video backgrounds or added UI frameworks.

The requested ui-ux-pro-max skill informed the accessibility/interaction review. Brand-matching rules and tokens are in [the design master](design-system/h-space/MASTER.md); implementation details are in [the frontend guide](docs/frontend.md).

The refresh passed 54 existing tests, page-template compilation, six JavaScript syntax checks and calculated contrast checks for the main text/action/control pairs. The loopback server served the new login, background and shared controls with HTTP 200. Browser access was unavailable; desktop/mobile rendered layouts and interactive visual checks at 375/768/1024/1440px remain unverified. The owned preview server was stopped after verification. After starting the project, use Ctrl+F5 to reload updated styles/scripts. Publishing the source does not deploy the application; cloud deployment remains deferred.

## Compact cards and interaction

The frontend-design refinement makes the vehicle grid fit **five cards at laptop viewport widths of 1200 CSS pixels and above**. It uses four columns at 1024–1199px, three at 800–1023px, two at 561–799px and one at 560px or below. Browser zoom changes the available CSS viewport width. Cards use smaller spacing and plate headings while keeping photo/removal controls at least 44px high; long text and footer actions wrap.

On a fine mouse pointer, cards lift slightly, tilt by at most 1.5 degrees per axis and show a soft orange highlight. Pointer movement is batched into one animation frame; tilt stops over action buttons and resets on leaving, scrolling, resizing, rerendering or hiding the page. Touch and keyboard access use native links/buttons, press feedback and visible focus. Nothing becomes accessible only on hover.

Buttons and focused fields provide clearer feedback; save buttons expose busy state and a spinner. Opening details or the add dialog has a short transition. Sign-in uses one coordinated entrance; no continuous background animation was added. Reduced-motion preferences suppress these effects, including changes made while a page is open. Decorative section numbers and the sign-in access index were replaced by meaningful icons/labels. Data, API and database behavior are unchanged.

Validation for this refinement: 14 focused health/vehicle HTTP tests, all seven JavaScript syntax checks and isolated interaction-controller checks passed. Controller checks covered frame batching, bounded tilt, touch exclusion, action-button stability, reset/cancellation and live reduced-motion changes. Native Windows Chrome review reached wide and narrow windows, English/Arabic and dark/light workspace views with existing data. The final narrow-heading adjustment remains visually unverified: Computer Use stopped when it could not reliably verify the browser URL. A full five-occupied-card row, exact viewport sizes, pointer animation appearance and physical phone testing remain outstanding. No sample inventory was added for the review. Reload the updated interface with Ctrl+F5. Source publication does not migrate local data or deploy the application.

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

Each gallery image and document has a Delete button with a permanent-deletion confirmation. All four signed-in users can delete attachments. The card has a separate Remove card photo action, which leaves gallery files intact. Deletion requires CSRF protection and scopes the attachment to its vehicle. Deleted preview/download links return 404; repeating a deletion returns 404.

Metadata removal and a durable file-cleanup entry commit in one PostgreSQL transaction. The file is then removed from the private disk directory. If disk cleanup fails, the attachment is already inaccessible and its cleanup entry remains for retry. An already-open download may finish. Deletion cannot be undone through the application; separately retained backups are unaffected.

Retry deferred file cleanup with `python manage.py cleanupfiles` (up to 100 entries per invocation). This processes only queued keys, preserves any still-referenced file, and never scans/deletes unrelated uploads. No background worker is configured. Card-photo replacement uses the same retry mechanism.

There is no vehicle deletion workflow, reservation system, accounting or maintenance workflow.

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

In pgAdmin, refresh Databases, open **limousine_local → Schemas → public → Tables**. Right-click a table, then View/Edit Data → All Rows. The seven application tables are:

| Table | Responsibility |
| --- | --- |
| limo_vehicle | Agreed vehicle text fields and creation time |
| limo_attachment | Gallery/file metadata |
| limo_vehicle_cover | Independent card photo metadata |
| hspace_user | Four UUID accounts, role and soft-delete status |
| hspace_session | Hashed session tokens and expiry |
| hspace_schema_migration | Applied schema versions |
| hspace_file_cleanup | Durable pending removals of private file bytes |

```sql
SELECT id, plate_number, vehicle_type, driver_name,
       chassis_number, manufacture_year, created_at
FROM public.limo_vehicle ORDER BY id;
```

The conversion removed Django source, configuration, packages and old authentication/framework tables, including the temporary legacy schema. Core vehicle table names and identifiers were preserved. Ignored emergency backups under `.local/backups/` contain pre-conversion snapshots; they are not used by the running app. Backup restoration has not been tested. The current migration command initializes only the FastAPI schema and is idempotent; it is not an importer for older installations.

Responsibilities remain separated: business rules in domain, use cases/contracts in application, PostgreSQL/files/passwords/schema in infrastructure, and HTTP/templates/assets in presentation. `manage.py` is a small project CLI, not a framework dependency. It supports runserver, check, test, migrate, cleanupfiles, setoperator and a compatibility collectstatic command (no build is needed). Local schema changes are restricted to the configured loopback `limousine_local` database; do not run migrations against an unintended environment.

Schema version 2 adds the cleanup queue and validates required vehicle fields, bounded positive file sizes, supported file kinds, safe unique storage keys and session hashes. It removes an inherited duplicate index and indexes session expiry. Upgrading an existing local database takes a private backup first; invalid historical rows stop the upgrade rather than being silently altered. The vehicle list now batches metadata reads into three queries instead of adding two queries per vehicle.

For an existing checkout, stop the development server, run `python manage.py migrate` in the configured environment, then restart it. The deletion feature and card-photo replacement need schema version 2. `manage.py cleanupfiles` is also available to retry deferred file removal.

Run `python scripts/check_database.py` for a read-only local audit of role privileges, expected schema versions/constraints/indexes, file references and byte sizes. It prints counts/findings without row contents or secrets. Run filesystem checks while uploads/deletions are idle. This does not establish production readiness. The local application role owns its schema for setup; separate migration/runtime roles and tested backup restoration remain production work.

## Verification

```powershell
.\.runtime\python\python.exe manage.py check
.\.runtime\python\python.exe manage.py test
.\.runtime\python\python.exe scripts/check_readme.py
git diff --check
```

The conversion passed 48 isolated tests and compiled all four page templates. Real local PostgreSQL integration checks passed for all four existing passwords, UUID/roles, admin-only account changes, soft deletion/restoration, session revocation/expiry, CSRF, vehicle creation/editing, independent card photos, image/PDF/TXT/DOCX/XLSX previews and private downloads. Test fixtures were removed. Existing business rows, password hashes and attachment bytes were compared before/after and preserved. Removal of the legacy schema and an idempotent schema rerun were also verified. A fresh Uvicorn process returned HTTP 200 for live health, real PostgreSQL readiness and the branded login page after cleanup; the project interpreter could no longer import the removed framework. The verification server was stopped afterward. All four JavaScript files passed syntax checks.

The opt-in real database check is `python scripts/verify_local.py`. It requires the intended local database and current private credentials note. It temporarily changes a member's status and revokes sessions, then restores account status and removes its own records. Run it when other users are not working.

Deletion-specific integration checks are in `python scripts/verify_deletion.py`. They use temporary records/files and a short-lived member session, exercise rollback and disk failure/retry, then compare existing business rows/accounts/file hashes and remove their own fixtures. Run while the local application is idle.

This addition passed 54 isolated tests and real PostgreSQL deletion checks, including member permissions, authentication/CSRF, wrong-vehicle rejection, repeated deletion, cover/gallery independence, replacement cleanup, rollback on a database error, disk failure/retry and actual CHECK, foreign-key and unique-storage-key constraints. Existing account/business rows and original file hashes remained unchanged. The final read-only audit found one existing vehicle, seven attachments, one cover, four users, zero pending cleanups, no missing/mismatched/unreferenced files and no missing expected constraints/indexes; the role has no superuser, create-database, create-role, replication or bypass-RLS privileges. Version 2 was applied successfully after a private backup, and rerunning the migration completed without reapplying the upgrade.

All four JavaScript files passed syntax checks. A fresh visual browser check was attempted but the computer-use safeguard stopped it because it could not establish the active Windows browser URL reliably; the updated controls/confirmation and narrow layout have not been visually verified. The loopback preview server was stopped afterward. Backup restore, restart, Docker and production checks remain outstanding. Cloud deployment remains deferred.

The test client currently emits an upstream deprecation warning about httpx; tests still pass. Browser appearance was checked on the previous UI version; the migrated backend has not yet received a fresh browser interaction check. Docker, backup restoration, device restart and deployment remain unverified.

CI runs the README change check, application/template check and isolated tests. It does not connect to the real local database. Documentation checking verifies that README changed, not that every statement is correct.

Docker/Compose supplies only the web service, binds its host port to loopback and uses a persistent media volume. A container needs separately configured PostgreSQL connectivity; its localhost is not the host computer. Production still needs HTTPS, rate limiting, operational hardening and tested database-plus-media backups.

## GitHub and local data

The repository contains application source, tests, documentation and setup examples. The README and supporting guides are maintained in English; the application's Arabic interface remains available.

Local connection secrets, account credentials, uploaded files, database backups, wallet files and the local Python runtime are excluded from Git. Checkout-local design skills under .agents/ and their skills-lock.json are also excluded; they are authoring tools and are not required to run the application. Cloning or pulling the repository does not restore the local database or attachments. Set up a private environment separately using the steps above. Pushing source to GitHub does not deploy the application or move local data to the cloud.

See [architecture](docs/architecture.md), [frontend](docs/frontend.md) and [remaining work](docs/next-steps.md).
