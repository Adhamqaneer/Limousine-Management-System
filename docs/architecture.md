# Architecture

H SPACE uses FastAPI/Uvicorn and PostgreSQL only. Cloud deployment is deferred.

- **domain** defines agreed vehicle fields and validation, UUID user identity, ADMIN/MEMBER roles and protected account status rules.
- **application** contains VehicleService, AccountService and repository contracts.
- **infrastructure** implements psycopg repositories, local private file storage, bounded document preview, PBKDF2 password verification, session persistence and versioned SQL schema.
- **presentation/web** adapts HTTP requests to services, validates CSRF, handles safe errors and serves Jinja2 templates/static assets.
- **config/runtime.py** loads private environment settings and validates production requirements.

Composition is in presentation/web/app.py. Every business route requires a valid server-side session; user management additionally requires ADMIN. Raw session tokens stay in HttpOnly cookies; their SHA-256 hashes and absolute 12-hour expiry are persisted. Account deactivation, soft deletion and password changes revoke sessions. Session checks reject inactive/deleted accounts on every request.

Four account slots are constrained in the database. User IDs are UUIDs; vehicle/attachment IDs retain their existing numeric values. Role values are a Python StrEnum and database CHECK constraint. Soft-delete/date/active consistency and a single ADMIN are constrained. The owner account is protected by domain rules and repository update restrictions.

The seven active tables are documented in [README](../README.md). Vehicle covers and gallery attachments have independent records. Private file bytes live under media/vehicles; parameterized SQL stores metadata only. Schema versions are applied transactionally and idempotently in the intended local database, with a private backup before upgrading an existing installation to version 2. The framework conversion preserved business rows/files/password hashes. Ignored emergency backups are not runtime dependencies.

Attachment deletion uses a vehicle-scoped DELETE RETURNING and atomically enqueues the key in hspace_file_cleanup. Cover removal/replacement serialize on the vehicle row independently of gallery attachments. After commit, FileCleanup removes unreferenced bytes and the queue entry. Disk/commit failures retain the entry for idempotent retry with manage.py cleanupfiles. A referenced key is never unlinked. There is no distributed database/disk transaction, automated worker or application undo. List metadata reads use three batch queries.

Version 2 strengthens file metadata and required-field constraints, removes a duplicate foreign-key index and indexes session expiry. The local application role owns its schema; distinct migration/runtime roles and tested backup restoration remain production requirements.

Missing configuration/database access returns generic unavailable responses; there is no alternate runtime repository. Tests inject mocks only. Sensitive database exceptions and request bodies are not returned or logged intentionally. Static assets are public; uploads are served only through authenticated handlers with no-store and nosniff headers.

The Studio visual refresh is confined to presentation: shared header/icon partials, semantic CSS, translated page controls and a local decorative Camry asset. Domain/application/persistence behavior and schema versions are unchanged by that refresh. interactions.js is a presentation-only controller for pointer response and detail opening, using delegated events and cancellation; app.js emits card-rerender/detail-ready events. It does not access persistence or change business behavior. The visual system is documented in docs/frontend.md and design-system/h-space/MASTER.md.

See [README](../README.md) for commands, actual verification and production limitations.
