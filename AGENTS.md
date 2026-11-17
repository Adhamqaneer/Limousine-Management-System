# Project instructions

## Scope and architecture

- Read `README.md` before changing this project. Work in the Limousine Management System checkout, not a neighbouring project.
- The owner has chosen local-first PostgreSQL instead of Oracle. PostgreSQL is the only runtime database. Do not add SQLite, browser-local business storage, or runtime fake repositories as a fallback. Defer server deployment.
- Keep business rules in `domain`, use cases and persistence contracts in `application`, implementations in `infrastructure`, and HTTP/UI adaptation in `presentation`.
- Vehicle fields are fixed and agreed with the owner. The agreed fields are owner name, owner phone, driver name, driver phone, vehicle type, vehicle model (stored as manufacture_year), chassis number and plate number, all text. Names/type accept Arabic or English letters and spaces; owner phone accepts digits; driver phone/model accept ASCII digits; chassis accepts ASCII letters/digits; plates accept ASCII digit groups separated by optional hyphens. Creation requires type and plate; remaining details are completed on the vehicle page. Do not invent additional business fields or workflows.
- Preserve English as the default UI language, Arabic/RTL, light/dark mode, and the simple vehicle-list/detail workflow.
- Upload the card photo from the vehicle card independently of the attachment gallery; gallery changes must never select or replace it. Provide authenticated document previews without sending files to external viewers.
- All four accounts may soft-delete vehicles, attachments and card photos. Only ADMIN may view the recycle bin/activity history and restore items. Retain file bytes and actor-attributed creation/deletion/restoration events; card-photo replacement archives the previous photo. Restoring a vehicle must not revive separately deleted files.
- All active accounts may assign drivers, correct the current driver and read/print driver periods. Keep current vehicle driver fields synchronized through the dedicated history workflow; ordinary vehicle edits must not overwrite them. Preserve phone snapshots, unknown legacy starts, handover boundaries and immutable before/after correction events.
- Keep `.env`, wallet files, local runtime, generated static files, uploads, backups and secrets out of Git. Never log sensitive connection details or request bodies.

## Maintain documentation with every change

- Update `README.md` as part of every change to code, configuration, dependencies, scripts or CI. The owner explicitly requires documentation to stay current without another reminder.
- Explain the actual effect: feature behavior, affected module responsibilities, setup/environment changes, commands, validation results and remaining limitations. If behavior is unchanged, update the relevant maintenance/validation note rather than making a meaningless date-only edit.
- Update `docs/architecture.md`, `docs/frontend.md` and `docs/next-steps.md` when their details change. README is the main project guide and must link to these supporting documents.
- Do not describe planned features as implemented. Passing isolated tests does not establish a successful real PostgreSQL connection, migration, Docker build, browser test or deployment.
- Run `python scripts/check_readme.py` before handing off code changes. CI also rejects implementation changes that omit README updates; this checks that documentation changed, not its factual accuracy.
- Treat documentation as part of completion. No extra owner confirmation is needed for routine README updates within the requested task.

## Verification and delivery

- Run focused tests appropriate to code changes. Full checks are documented in README. Do not run real PostgreSQL migrations without the intended configured environment.
- Keep development servers on loopback. Exactly four fixed account slots share vehicle access; Adham is ADMIN and alone manages member account status. Use FastAPI; do not restore the previous framework. All vehicle data and attachment routes require authentication. Production readiness must not be claimed.
- Report what was verified and what remains unverified. Do not assume a local commit was pushed: distinguish local commit, remote push and deployment, and verify the requested action.
