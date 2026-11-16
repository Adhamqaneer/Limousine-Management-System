# Remaining work

The current scope is a local FastAPI/PostgreSQL trial with four accounts. Adham is ADMIN; the other three share vehicle permissions. The framework conversion, account/session behavior, private files and core vehicle workflows passed isolated and real database integration checks. Old framework source/packages/tables were removed; business rows, file bytes and password hashes were preserved.

Attachment/card-photo deletion now includes confirmation, vehicle-scoped authenticated CSRF-protected routes and durable retry of failed disk cleanup. Version 2 strengthens actual file metadata constraints and indexes; scripts/check_database.py audits the local database/files without writes. See README for completed validation. The retry command is manual; background cleanup scheduling remains deferred.

The H SPACE Studio redesign now includes the requested Camry scene on sign-in/interior backgrounds, shared navigation, both themes/languages and accessible password visibility. Automated/template/static-resource checks passed; browser access was unavailable.

Before wider use, perform a fresh browser check of the converted backend, including the Studio backgrounds, Show/Hide password, Team, language/theme, narrow layout, deletion and document previews. The compact-card interaction refinement now uses five columns from 1200 CSS pixels, with fewer columns on narrower screens. Native Chrome review covered wide/narrow windows and language/theme controls, but the browser URL safeguard stopped further input. Recheck the final narrow-heading correction, pointer appearance and a full five-occupied-card row. Check 375/768/1024/1280/1366/1440px, landscape and reduced motion. Test a physical phone separately; development currently stays on loopback. Also test PostgreSQL/device restart and restoration of database plus media backups. Separate runtime and migration database roles before production.

Cloud deployment is deferred. It will need explicit database/file destinations, HTTPS, secrets, login rate limiting, operational monitoring, persistent storage and tested backups. Docker has been updated but not built or run. Existing local data will not move automatically. Backup scheduling remains future work.

No reservations, accounting, maintenance or new vehicle fields are part of this change. Actual validation and setup commands are in [README](../README.md).
