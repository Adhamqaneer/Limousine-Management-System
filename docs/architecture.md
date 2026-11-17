# Architecture

H SPACE uses FastAPI/Uvicorn and PostgreSQL only. Cloud deployment is deferred.

- **domain** defines agreed vehicle fields and validation, UUID user identity, ADMIN/MEMBER roles and protected account status rules.
- **application** contains VehicleService, AccountService and repository contracts.
- **infrastructure** implements psycopg repositories, local private file storage, bounded document preview, PBKDF2 password verification, session persistence and versioned SQL schema.
- **presentation/web** adapts HTTP requests to services, validates CSRF, handles safe errors and serves Jinja2 templates/static assets.
- **config/runtime.py** loads private environment settings and validates production requirements.

Composition is in presentation/web/app.py. Every business route requires a valid server-side session; user management additionally requires ADMIN. Raw session tokens stay in HttpOnly cookies; their SHA-256 hashes and absolute 12-hour expiry are persisted. Account deactivation, soft deletion and password changes revoke sessions. Session checks reject inactive/deleted accounts on every request.

Four account slots are constrained in the database. User IDs are UUIDs; vehicle/attachment IDs retain their existing numeric values. Role values are a Python StrEnum and database CHECK constraint. Soft-delete/date/active consistency and a single ADMIN are constrained. The owner account is protected by domain rules and repository update restrictions.

The ten active tables are documented in [README](../README.md). Vehicle covers and gallery attachments have independent records. Private file bytes live under media/vehicles; parameterized SQL stores metadata only. Schema versions are applied transactionally and idempotently in the intended local database, with a private backup before upgrading an existing installation to the latest schema version. The framework conversion preserved business rows/files/password hashes. Ignored emergency backups are not runtime dependencies.

Attachment deletion uses a vehicle-scoped DELETE RETURNING and atomically enqueues the key in hspace_file_cleanup. Cover removal/replacement serialize on the vehicle row independently of gallery attachments. After commit, FileCleanup removes unreferenced bytes and the queue entry. Disk/commit failures retain the entry for idempotent retry with manage.py cleanupfiles. A referenced key is never unlinked. There is no distributed database/disk transaction, automated worker or application undo. List metadata reads use three batch queries.

Version 2 strengthens file metadata and required-field constraints, removes a duplicate foreign-key index and indexes session expiry. The local application role owns its schema; distinct migration/runtime roles and tested backup restoration remain production requirements.

Missing configuration/database access returns generic unavailable responses; there is no alternate runtime repository. Tests inject mocks only. Sensitive database exceptions and request bodies are not returned or logged intentionally. Static assets are public; uploads are served only through authenticated handlers with no-store and nosniff headers.

The Studio visual refresh is confined to presentation: shared header/icon partials, semantic CSS, translated page controls and a local decorative Camry asset. Domain/application/persistence behavior and schema versions are unchanged by that refresh. interactions.js is a presentation-only controller for pointer response and detail opening, using delegated events and cancellation; app.js emits card-rerender/detail-ready events. It does not access persistence or change business behavior. The visual system is documented in docs/frontend.md and design-system/h-space/MASTER.md.

See [README](../README.md) for commands, actual verification and production limitations.

Approximate search is a presentation-only pure ranking helper (static/web/search.js). It operates on authorized vehicles already fetched by app.js, without persistence, extra requests or normalization of stored records. Domain and PostgreSQL matching are unchanged.

Schema version 3 adds owner_name/owner_phone/driver_phone to limo_vehicle, with empty defaults and phone CHECK constraints. Domain rules validate the eight agreed text fields; the repository maps new contacts, and the authenticated HTTP adapter exposes them. Existing manufacture_year represents the vehicle model. Existing rows and files are retained; partial edits validate changed values only, allowing historical formats to survive unrelated edits. The local upgrade and rollback-only PostgreSQL integration checks passed.

Vehicle reporting adds an authenticated presentation page at /reports/vehicles/ and reuses GET /api/vehicles/ through the existing application/repository. Selection and projection are ephemeral browser presentation state with an eight-field allowlist. Native printing/PDF saving is local to the browser; it adds no persistence, write route or migration. All fixed accounts share report access.

Main-list owner/model/type filters are presentation-only. vehicle-filters.js derives exact-match facets from the existing authenticated list; app.js intersects these before search ranking. They add no application use case, SQL, endpoint, migration or persistent selection. Print reports remain independent and include all vehicles.

Filtered report scope is an allowlisted, bounded client URL fragment containing only owner/model/type/search criteria. The report still reads the authenticated list through existing application/persistence contracts, then reuses list presentation helpers for matching/order; it adds no write route or database changes. Native owner suggestions are presentation adaptation over the same list, with exact trimmed name grouping and no new owner entity.

Office stationery is presentation-only: a shared print partial, report CSS and dynamic selected-column span in vehicle-report.js. All/filtered reports share the same layout, with a repeating table head and fixed print watermark. It changes no stored records or original uploaded file bytes.

Schema 4 adds retained deletion state/creator attribution to the three business tables and hspace_activity (eight active tables total). Domain/application recovery rules enforce ADMIN-only restoration/history; all active users may soft-delete. Repository mutations lock parents before children, transact audit with state, retain covers on replacement and prevent physical business-row deletion/activity mutation with SQL triggers. Parent deletion masks children; restoration does not revive independently deleted children. All ordinary file/list/report reads exclude deleted state. Cleanup treats deleted references as live references. Audit is not independently tamper-proof against a schema owner.

The deleted-item read model now includes has_current_cover, allowing admin recovery UI to offer current-cover soft deletion before restoring an archived photo. It reuses existing commands/authorization and adds no schema or route.

Schema 5 introduces driver periods and immutable assignment/correction snapshots, bringing the runtime table count to ten. DriverService validates calendar dates and names/phones; PostgresDriverRepository locks the active vehicle, maintains a single current assignment, prevents overlapping handovers and syncs the cached current vehicle fields atomically. Generic vehicle PATCH cannot edit driver identity; a database guard rejects unsynchronized direct updates. History is masked by parent deletion and retained for recovery. Legacy driver values are seeded without invented start/creator/time. Driver lookup/printing are presentation adaptations over authenticated history use cases.
