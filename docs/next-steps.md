# Remaining work

The current scope is a local FastAPI/PostgreSQL trial with four accounts. Adham is ADMIN; the other three share vehicle permissions. The framework conversion, account/session behavior, private files and core vehicle workflows passed isolated and real database integration checks. Old framework source/packages/tables were removed; business rows, file bytes and password hashes were preserved.

Before wider use, perform a fresh browser check of the converted backend, including Team, language/theme, narrow layout and document previews. Test a physical phone separately; development currently stays on loopback. Also test PostgreSQL/device restart and restoration of database plus media backups.

Cloud deployment is deferred. It will need explicit database/file destinations, HTTPS, secrets, login rate limiting, operational monitoring, persistent storage and tested backups. Docker has been updated but not built or run. Existing local data will not move automatically. Backup scheduling remains future work.

No reservations, accounting, maintenance or new vehicle fields are part of this change. Actual validation and setup commands are in [README](../README.md).
