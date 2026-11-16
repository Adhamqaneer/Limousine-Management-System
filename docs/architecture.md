# Architecture

H SPACE uses FastAPI/Uvicorn and PostgreSQL only. Cloud deployment is deferred.

- **domain** defines agreed vehicle fields and validation, UUID user identity, ADMIN/MEMBER roles and protected account status rules.
- **application** contains VehicleService, AccountService and repository contracts.
- **infrastructure** implements psycopg repositories, local private file storage, bounded document preview, PBKDF2 password verification, session persistence and versioned SQL schema.
- **presentation/web** adapts HTTP requests to services, validates CSRF, handles safe errors and serves Jinja2 templates/static assets.
- **config/runtime.py** loads private environment settings and validates production requirements.

Composition is in presentation/web/app.py. Every business route requires a valid server-side session; user management additionally requires ADMIN. Raw session tokens stay in HttpOnly cookies; their SHA-256 hashes and absolute 12-hour expiry are persisted. Account deactivation, soft deletion and password changes revoke sessions. Session checks reject inactive/deleted accounts on every request.

Four account slots are constrained in the database. User IDs are UUIDs; vehicle/attachment IDs retain their existing numeric values. Role values are a Python StrEnum and database CHECK constraint. Soft-delete/date/active consistency and a single ADMIN are constrained. The owner account is protected by domain rules and repository update restrictions.

The six active tables are documented in [README](../README.md). Vehicle covers and gallery attachments have independent records. Private file bytes live under media/vehicles; parameterized SQL stores metadata only. The initial schema migration is transactional and idempotent, restricted to the intended local database. The one-time framework conversion preserved business rows/files/password hashes and removed old framework tables and source. Ignored emergency backups are retained separately and are not runtime dependencies.

Missing configuration/database access returns generic unavailable responses; there is no alternate runtime repository. Tests inject mocks only. Sensitive database exceptions and request bodies are not returned or logged intentionally. Static assets are public; uploads are served only through authenticated handlers with no-store and nosniff headers.

See [README](../README.md) for commands, actual verification and production limitations.
