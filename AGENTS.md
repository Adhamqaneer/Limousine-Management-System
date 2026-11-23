# AI project rules

- Read README.md first. Stay in this checkout; preserve behavior unless the owner requests changes.
- Use FastAPI and PostgreSQL only for application services and data. Keep development and the Windows desktop preview on loopback. Distribution packaging is deferred; do not add fallback business stores.
- Keep rules in domain, use cases/contracts in application, persistence in infrastructure and HTTP/UI in presentation. Fixed text fields and validation are in docs/architecture.md.
- One office sign-in, H space, covers all features including recovery and activity. Preserve former user IDs and names for historical attribution.
- Retain original file bytes and actor-attributed events. Card photos, vehicle galleries, driver documents and office files are independent. Restoring a vehicle must not revive separately deleted files.
- Change current driver name/phone through history only. Preserve phone snapshots, unknown starts, handover boundaries, gaps and immutable correction/end events.
- Keep data/file routes authenticated, mutations CSRF-protected, previews local, English/Arabic RTL and both themes intact.
- Never commit/log .env, credentials, account files, uploads, runtime or backups. Do not inspect secrets for routine refactoring.
- Update README.md and affected docs with changes. Keep README focused on setup/use; put technical details in docs/.
- Run appropriate tests and python scripts/check_readme.py. Use only the intended environment for migrations. Distinguish isolated, real-database and browser checks, commits, pushes and deployment in the handoff.
