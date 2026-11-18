# Architecture

## Follow one request

1. manage.py starts presentation/web/app.py.
2. The app creates repositories/services, then registers feature routes.
3. A route checks authentication/CSRF, reads its form and calls a service.
4. The service applies domain rules and calls its repository contract.
5. The PostgreSQL adapter executes parameterized SQL in a short transaction. The route returns public JSON or a Jinja page.

## Where to change things

| Location | Responsibility |
| --- | --- |
| domain/ | Plain records, validation, roles and driver-date rules |
| application/ | Use cases and persistence contracts; no HTTP/SQL |
| infrastructure/ | PostgreSQL, private files, previews, ZIPs, password hashes and schema |
| presentation/web/app.py | Wire dependencies and register routes |
| presentation/web/routes/ | Accounts, vehicles, drivers, office, recovery and health endpoints |
| presentation/web/requests.py | Bounded JSON forms and vehicle field names |
| presentation/web/serializers.py | Public JSON; no storage keys/password hashes |
| presentation/web/file_handlers.py | Shared private upload/rename/preview/download handling |
| presentation/web/security.py | Sessions, administrator checks and signed CSRF |
| presentation/web/http_errors.py | Safe errors and security headers |
| config/runtime.py | Private .env settings |

Routes are small functions registered by feature. Tests replace repositories/services at the application boundary.

## Fixed vehicle fields

All eight fields are text; leading zeroes matter. Creation requires type and plate. Other fields can be completed later.

| UI order | Stored field | Accepted input |
| --- | --- | --- |
| Vehicle number | plate_number | ASCII digit groups, optionally separated by hyphens |
| Owner name | owner_name | Arabic/English letters and spaces |
| Driver name | driver_name | Same name rule; history workflow only |
| Vehicle type | vehicle_type | Arabic/English letters and spaces |
| Vehicle model | manufacture_year | ASCII digits |
| Chassis number | chassis_number | ASCII letters/digits |
| Owner phone | owner_phone | ASCII, Arabic or Persian digits |
| Driver phone | driver_phone | ASCII digits; history workflow only |

Arabic combining marks are allowed after a letter. Unrelated edits preserve legacy values; changed fields use current validation.

## PostgreSQL tables (schema 9)

| Table | Purpose |
| --- | --- |
| hspace_user | Four UUID accounts, hashed passwords, ADMIN/MEMBER and status |
| hspace_session | SHA-256 token hashes and absolute expiry |
| limo_vehicle | Vehicle fields, current driver cache and deletion actors |
| limo_attachment | Vehicle gallery or driver-period file metadata |
| limo_vehicle_cover | Independent card photos and archived replacements |
| hspace_office_attachment | Office files, independent of vehicles/drivers |
| hspace_driver_assignment | Driver name/phone snapshots and work periods |
| hspace_driver_change | Immutable ASSIGN/CORRECT/END snapshots |
| hspace_activity | Immutable CREATE/RENAME/DELETE/RESTORE actor events |
| hspace_file_cleanup | Retry queue for unreferenced failed uploads |
| hspace_schema_migration | Applied schema versions |

Migrations are transactional/idempotent and restricted to the configured loopback limousine_local database. Existing upgrades require a private pg_dump backup. Foreign keys, metadata/deletion checks, partial unique indexes and retention triggers protect relationships/history. The local role owns its schema; this is not independently tamper-proof audit storage.

## Invariants

- Sessions expire after 12 hours. Disabling/deleting an account or changing its password revokes access. Cookies are HttpOnly; mutations require signed, session-bound CSRF.
- All active accounts can delete. Metadata/bytes remain; only ADMIN restores. Parent restoration does not undo separate child deletion.
- Driver documents use a composite period/vehicle foreign key; NULL assignment means the vehicle gallery. Office documents use their own table and a nullable-vehicle activity scope.
- Driver changes lock the vehicle first, update period/current cache and append snapshots atomically. Unknown starts stay unknown. ended_on is exclusive; the displayed last working day is inclusive. Gaps before replacements are supported.
- Uploads use generated UUID filenames in office/photos|files, vehicles/vehicle-ID/photos|files|covers, or a named drivers/period folder. Limit: 10 MiB/file and 25 MP/image. JPG/PNG/WebP/PDF/TXT/DOCX/XLSX are validated locally. Gallery changes never select a card photo.
- Rename preserves the extension and rejects stale names. ZIPs contain active originals from one section only; temporary storage closes on success/failure.

## Media organization

infrastructure/media_paths.py owns safe directory labels and shared storage-key patterns. media_layout.py coordinates copies, metadata updates and cleanup. Driver repositories receive this organizer so assignment, correction and ending also update period folder names. Upload handlers acquire the same PostgreSQL advisory lock, preventing uploads from racing date changes. Vehicle creation prepares its private subdirectories.

Copies are completed before metadata commits; old paths enter the existing cleanup queue in that transaction. Cleanup removes old duplicates only after checking all file references. Failed/uncertain commits retain referenced originals; interrupted work can leave extra copies rather than lose the source. Only empty retired directories are removed. Application URLs, attachment names, audit actors, history snapshots and soft-deletion state are unchanged. File paths use normalized Windows-safe driver labels with bounded names, years and period-ID suffixes; display names remain unchanged.

Schema 9 widens file-key checks without adding tables. It accepts existing keys for compatibility and scoped organized keys for new work. scripts/organize_media.py backs up the intended local database/media, applies the schema if needed and relocates existing originals, including deleted files. Run it only while the app is idle. No automated tests were executed for this change at the owner's request.
