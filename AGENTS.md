# Project instructions

## Scope and architecture

- Read `README.md` before changing this project. Work in the Limousine Management System checkout, not a neighbouring project.
- Oracle Database is the only runtime database. Do not add SQLite, PostgreSQL, browser-local business storage, or runtime fake repositories as a fallback.
- Keep business rules in `domain`, use cases and persistence contracts in `application`, implementations in `infrastructure`, and HTTP/UI adaptation in `presentation`.
- Vehicle fields are fixed and agreed with the owner. The plate number is currently the only agreed field. Do not invent additional business fields or workflows.
- Preserve English as the default UI language, Arabic/RTL, light/dark mode, and the simple vehicle-list/detail workflow.
- Keep `.env`, wallet files, local runtime, generated static files, uploads, backups and secrets out of Git. Never log sensitive connection details or request bodies.

## Maintain documentation with every change

- Update `README.md` as part of every change to code, configuration, dependencies, scripts or CI. The owner explicitly requires documentation to stay current without another reminder.
- Explain the actual effect: feature behavior, affected module responsibilities, setup/environment changes, commands, validation results and remaining limitations. If behavior is unchanged, update the relevant maintenance/validation note rather than making a meaningless date-only edit.
- Update `docs/architecture.md`, `docs/frontend.md` and `docs/next-steps.md` when their details change. README is the main project guide and must link to these supporting documents.
- Do not describe planned features as implemented. Passing isolated tests does not establish a successful real Oracle connection, migration, Docker build, browser test or deployment.
- Run `python scripts/check_readme.py` before handing off code changes. CI also rejects implementation changes that omit README updates; this checks that documentation changed, not its factual accuracy.
- Treat documentation as part of completion. No extra owner confirmation is needed for routine README updates within the requested task.

## Verification and delivery

- Run focused tests appropriate to code changes. Full checks are documented in README. Do not run real Oracle migrations without the intended configured environment.
- Keep development servers on loopback. Authentication and user authorization are not implemented yet; production readiness must not be claimed.
- Report what was verified and what remains unverified. Do not assume a local commit was pushed: distinguish local commit, remote push and deployment, and verify the requested action.
