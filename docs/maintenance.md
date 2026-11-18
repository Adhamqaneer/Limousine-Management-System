# Maintenance

## Routine checks

Use the Python interpreter configured for the project; on this checkout that can be .runtime/python/python.exe. The PowerShell launcher selects it automatically for check/test.

| Command | What it checks |
| --- | --- |
| python manage.py check | Imports FastAPI and compiles all eight page templates |
| python manage.py test | Isolated Python domain/service/HTTP/storage tests |
| node scripts/test_frontend.cjs | Browser-script syntax and all frontend harnesses; no npm install |
| python scripts/check_readme.py | Implementation changes include a README update |
| python scripts/check_database.py | Read-only local schema/role/index/constraint/file audit |
| git diff --check | Whitespace problems in the patch |

Keep Python at four-space indentation and web files at two spaces (see .editorconfig). Long calls/conditions should wrap; keep validation and transaction decisions explicit. Black (100-column style), Ruff (F/E9/I) and Prettier were used as local authoring tools for this refactoring. They are not runtime dependencies. Keep meaningful explanations of boundaries/security; remove comments that just narrate the next line.

## Optional real-database verification

These scripts are for the intended local database while the app is idle. They may back up/upgrade an older schema, create rollback-only fixtures and use temporary media. Rollback can still advance sequences. Read their scope before running:

- scripts/verify_recycling.py: recoverable deletion, actor history and administrator recovery.
- scripts/verify_drivers.py: assignment/correction, period boundaries and snapshots.
- scripts/verify_attachment_names.py: rename conflicts, original downloads/ZIPs and audit rollback.
- scripts/verify_driver_documents.py: ending periods, document scope and current-driver synchronization.
- scripts/verify_office_files.py: independent office documents and recovery/audit.

No real-database migration or fixture mutation was run for this refactoring; only the read-only audit was used. Historical migrations are kept because fresh installation/upgrades need them. Never remove retained rows/files to clean up test fixtures.

Navigation follow-up: eight focused navigation/report/asset tests passed after fixing merged active-link classes. All six destinations retain their shared layout class and current-page state. Native visual verification remains outstanding.

## Refactoring review results

- 101 Python tests passed.
- 17 browser scripts passed syntax checks; all 11 frontend harness files passed.
- Eight templates compiled; all 49 route paths, names and HTTP methods matched the pre-refactor snapshot.
- Read-only PostgreSQL audit passed: schema 8, expected constraints/indexes/triggers, synchronized driver caches and no missing/invalid/unreferenced files.
- Python formatting checked AST equivalence; formatted repository SQL retained the same non-whitespace tokens. Queries that failed that comparison were left unchanged.
- Native browser/mobile layout and actual print/download checks remain unverified. Docker was not built/run. CI configuration was updated but no remote CI run, commit, push or deployment was performed.

Removed after checking references: the unused environment example (setup writes .env directly), the retired conversion verifier, its unrelated duplicate deletion-verifier alias, the unreferenced ASGI shortcut and the no-op collectstatic command. The existing ASGI target remains limousine.presentation.web.app:app. AGENTS.md was shortened to project-specific AI rules; no application code depends on it.

Source PNG artwork, versioned SQL migrations, Docker/Compose and the separate feature verifiers are retained deliberately: editable source, upgrade path, optional packaging and different integration scopes are useful even though they are not needed on every startup. Secrets, private data and local tooling remain ignored by Git.

## Media folder organization

The current schema is 9. Existing originals were organized after a private database dump and media ZIP backup. No tests were run for this feature at the owner's request; earlier results above predate it. To organize another intended local checkout, stop the app and run python scripts/organize_media.py with its configured interpreter. The command backs up first; repeated runs keep already-correct paths. Names/period dates automatically update through the normal driver workflow. A locked file can leave a queued old copy; cleanupfiles retries it later. Retain both database and media backups together.
