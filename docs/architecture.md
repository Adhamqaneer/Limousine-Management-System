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
| presentation/web/security.py | Office sessions and signed CSRF |
| presentation/web/http_errors.py | Safe errors and security headers |
| config/runtime.py | Private .env settings |

Routes are small functions registered by feature. Tests replace repositories/services at the application boundary.

## Fixed vehicle fields

All eight fields are text; leading zeroes matter. Creation requires type and plate. Other fields can be completed later.

| UI order | Stored field | Accepted input |
| --- | --- | --- |
| Vehicle number | plate_number | ASCII digit groups separated by at least one hyphen when adding or changing the number |
| Owner name | owner_name | Arabic/English letters and spaces |
| Driver name | driver_name | Same name rule; history workflow only |
| Vehicle type | vehicle_type | Arabic/English letters and spaces |
| Vehicle model | manufacture_year | ASCII digits |
| Chassis number | chassis_number | ASCII letters/digits |
| Owner phone | owner_phone | ASCII, Arabic or Persian digits |
| Driver phone | driver_phone | ASCII digits; history workflow only |

Arabic combining marks are allowed after a letter. Unrelated edits preserve legacy values; changed fields use current validation.

## PostgreSQL tables (schema 14)

| Table | Purpose |
| --- | --- |
| hspace_user | UUID actor identities and names, including former users |
| hspace_operator | Singleton credential with password hash and a reference to the current actor |
| hspace_session | SHA-256 token hashes and absolute expiry |
| limo_vehicle | Vehicle fields, current driver cache and deletion actors |
| limo_attachment | Vehicle gallery or driver-period file metadata |
| limo_vehicle_cover | Independent card photos and archived replacements |
| hspace_office_attachment | Office files, independent of vehicles/drivers |
| hspace_driver_assignment | Driver name/phone snapshots and work periods |
| hspace_driver_change | Immutable ASSIGN/CORRECT/END snapshots |
| hspace_attachment_category | Canonical document types, protected Other and merge destinations |
| hspace_category_alias | Global unique normalized names mapped to canonical types |
| hspace_activity | Immutable CREATE/RENAME/DELETE/RESTORE/LABEL/ALIAS/MERGE actor events |
| hspace_file_cleanup | Retry queue for unreferenced failed uploads |
| hspace_schema_migration | Applied schema versions |

Migrations are transactional/idempotent and restricted to the configured loopback limousine_local database. Existing upgrades require a private pg_dump backup. Foreign keys, metadata/deletion checks, partial unique indexes and retention triggers protect relationships/history. The local role owns its schema; this is not independently tamper-proof audit storage.

Schema 12 adds the singleton credential for H space, revokes legacy sessions and removes the former password hashes and role/status columns. It inserts a new actor ID and keeps all historical actor IDs and names. The first password is entered privately before the migration, which installs the credential in the same transaction as the schema change.

Schema 13 backs up the database and raises the size checks for vehicle and driver attachments, card photos and office attachments to 25 MiB. It preserves the operator credential and sessions.

Schema 14 indexes vehicle numbers and guards new and changed numbers in PostgreSQL, including concurrent requests. Comparison uses the stored number, preserving hyphens and leading zeros. Deleted vehicles keep their numbers. Existing duplicates keep their records and can be corrected to unused numbers. Duplicate assignments return `vehicle_number_in_use` (409).

## Invariants

- Sessions expire after 12 hours. Changing the office password revokes existing sessions. Cookies are HttpOnly; mutations require signed, session-bound CSRF.
- The signed-in operator can delete and restore. Metadata and file bytes remain. Parent restoration does not undo separate child deletion.
- Driver documents use a composite period/vehicle foreign key; NULL assignment means the vehicle gallery. Office documents use their own table and a nullable-vehicle activity scope.
- Driver changes lock the vehicle first, update period/current cache and append snapshots atomically. Unknown starts stay unknown. ended_on is exclusive; the displayed last working day is inclusive. Gaps before replacements are supported.
- Uploads use generated UUID filenames in office/photos|files, vehicles/vehicle-ID/photos|files|covers, or a named drivers/period folder. Limit: 25 MiB/file and 40 MP/image. JPG/PNG/WebP/PDF/TXT/DOCX/XLSX are validated locally. Gallery changes never select a card photo.
- Camera JPGs with an embedded preview (MPO) retain their original bytes. The 40 MP limit applies to the combined JPEG frames.
- Rename preserves the extension and rejects stale names. ZIPs contain active originals from one section only; temporary storage closes on success/failure.

## Media organization

infrastructure/media_paths.py owns safe directory labels and shared storage-key patterns. media_layout.py coordinates copies, metadata updates and cleanup. Driver repositories receive this organizer so assignment, correction and ending also update period folder names. Upload handlers acquire the same PostgreSQL advisory lock, preventing uploads from racing date changes. Vehicle creation prepares its private subdirectories.

Copies are completed before metadata commits; old paths enter the existing cleanup queue in that transaction. Cleanup removes old duplicates only after checking all file references. Failed/uncertain commits retain referenced originals; interrupted work can leave extra copies rather than lose the source. Only empty retired directories are removed. Application URLs, attachment names, audit actors, history snapshots and soft-deletion state are unchanged. File paths use normalized Windows-safe driver labels with bounded names, years and period-ID suffixes; display names remain unchanged.

Schema 9 widens file-key checks without adding tables. It accepts existing keys for compatibility and scoped organized keys for new work. scripts/organize_media.py backs up the intended local database/media, applies the schema if needed and relocates existing originals, including deleted files. Run it only while the app is idle. No automated tests were executed for this change at the owner's request.

## Attachment classification and ZIP downloads

Schema 10 adds non-null category foreign keys to vehicle, driver and office attachments, defaulting existing records to Other. The classification feature now applies to vehicle and driver attachments. Office uploads rely on the database default and office API responses omit the category. The existing office column and historical values are retained for schema compatibility. Names and aliases share a unique normalized registry (Unicode normalization, Arabic alef/marks/tatweel, case and punctuation). Similarity suggestions use canonical names and aliases. The signed-in operator decides whether similar names have the same meaning. Other cannot absorb named types or be merged.

Category writes and classified uploads acquire the same transaction advisory lock before resolving a category. Merges move active and deleted vehicle and driver attachment references and all aliases atomically, retain source category rows and append actor events. Stale upload IDs resolve through the merge chain. Original bytes, filenames, driver periods and deletion state do not change. This feature does not provide category deletion or an automatic merge undo.

The category download accepts explicit vehicle/category IDs, checks active parents and gallery-only attachments in a read-only repeatable snapshot, then builds one temporary ZIP. Driver/office files and card covers remain independent. Limits: 500 vehicles, 50 types, 1000 files and 1 GiB of original bytes per download. All supported original formats are included without rendering or conversion.

Each vehicle receives a safe, unique plate-number directory; duplicate filenames receive numbered suffixes. A UTF-8 _missing-documents.txt report identifies absent types. Archive creation finishes before sending any response and checks each file size, so missing/changed originals cannot produce a partial download. The existing archive response closes temporary storage after completion or disconnect. Category downloads require authentication and CSRF; the response is private/no-store.

The authenticated CSRF-protected POST /api/attachment-download/availability/ uses the same validated vehicle/category scope as ZIP selection. It aggregates active gallery counts without downloading files and returns all scoped vehicles, filling absent category counts with zero. This preview does not mutate records and does not replace the fresh authorization/selection used for the actual ZIP.

Schema 11 adds a transactional category-slot trigger. Each active vehicle-gallery named category permits one attachment across image/file kinds; Other, driver-period documents, office documents and card photos remain independent. Upload preflight rejects occupied slots before writing bytes, and the locked metadata transaction rechecks. Classification, merges and restoration are also guarded. Existing duplicates are retained; unrelated edits/no-op labels still work, while new occupancy conflicts return category_in_use (409). Category writes share the transaction advisory lock so simultaneous uploads cannot claim the same slot.
