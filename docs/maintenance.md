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

Keep Python at four-space indentation and web files at two spaces (see .editorconfig). Use one parameter per line for Python and JavaScript definitions with multiple parameters, including `self`, and one argument per line in calls with multiple arguments. Use trailing commas where the language permits them. Put each clause of a compound condition on its own line. Keep validation and transaction decisions explicit. Black, Ruff and Prettier are local authoring tools. Keep comments that explain boundaries or security decisions.

## Optional real-database verification

These scripts are for the intended local database while the app is idle. They may back up/upgrade an older schema, create rollback-only fixtures and use temporary media. Rollback can still advance sequences. Read their scope before running:

- scripts/verify_recycling.py: recoverable deletion, actor history and office recovery.
- scripts/verify_drivers.py: assignment/correction, period boundaries and snapshots.
- scripts/verify_attachment_names.py: rename conflicts, original downloads/ZIPs and audit rollback.
- scripts/verify_driver_documents.py: ending periods, document scope and current-driver synchronization.
- scripts/verify_categories.py: labels/aliases/merges, stale uploads, retained originals and category ZIP downloads; requires migrations already applied.
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

Source PNG artwork, versioned SQL migrations and the separate feature verifiers provide editable assets, database upgrades and targeted integration checks. Secrets, private data and local tooling remain ignored by Git.

## Pre-desktop code cleanup

The owner chose to remove Docker, Compose and the Docker build ignore file. Local operation uses the PowerShell launcher. JavaScript conditionals use blocks, and long conditions break onto separate lines. ZIP downloads share one routine for copying and checking original bytes. The attachment category UI no longer exports methods or sends events with no callers or listeners.

## Media folder organization

The folder organization was introduced in schema 9 (current schema: 10). Existing originals were organized after a private database dump and media ZIP backup. No tests were run for this feature at the owner's request; earlier results above predate it. To organize another intended local checkout, stop the app and run python scripts/organize_media.py with its configured interpreter. The command backs up first; repeated runs keep already-correct paths. Names/period dates automatically update through the normal driver workflow. A locked file can leave a queued old copy; cleanupfiles retries it later. Retain both database and media backups together.

## Attachment category downloads

Schema 10 adds category metadata; switching the mistaken attachment-print workflow to ZIP downloads needs no further schema migration. Existing data/classifications remain intact. The unused PDF renderer, its worker/dependency, print page/styles and their tests were removed. No installed private-runtime packages were deleted.

scripts/verify_categories.py exercises real PostgreSQL and authenticated HTTP using rolled-back fixtures and temporary media: category/alias/merge, stale upload IDs, deleted metadata, all attachment scopes, per-vehicle ZIP originals and missing documents. It compares the original rows/media afterward; sequences may advance on rollback. Category download HTTP, safe ZIP names, original bytes, limits and error cleanup have isolated tests. Frontend checks cover the simple download selection and preserve the existing reports. Native browser downloads remain unverified.

The static detector cannot resolve Jinja static() stylesheets. The categories and download templates use the shared 28-44px heading against 16px body text, so their file-scoped flat-type-hierarchy exceptions preserve the actual hierarchy. The exception for the deleted attachment-print template was removed.

Current download checks passed: 110 isolated Python tests, 20 browser-script syntax checks, 13 frontend harness files, all ten templates (59 routes), the rollback-only PostgreSQL ZIP verifier, README and whitespace checks. No additional schema change, commit, push or deployment was performed.

Category-management UI removal: removed categories.html, categories.js, the page GET route, management links and page-only styles. Category data and API behavior were preserved. Removed the stale detector exception for that deleted page.

Inline category creation and download availability reuse schema 10; no migration is needed. Focused UI coverage includes permanent options with Other last, upload/classification reuse, Arabic/English labels and scoped availability rows. The real-database verifier also checks positive/zero gallery counts while excluding separately deleted files and driver/office documents.

Inline creation/availability checks passed: 111 isolated Python tests, all 19 browser scripts and 13 frontend harnesses, nine page templates (59 routes), the rollback-only PostgreSQL verifier, README/whitespace and scoped detector checks. The detector still cannot resolve Jinja-linked stylesheets; no additional ignores were introduced. Native visual checks are not established by these automated results.

Vehicle category uniqueness (schema 11): an automatic private pg_dump backup precedes migration. Existing duplicate named-category groups are retained without recategorizing/deleting originals. New uploads, category changes, merges and restoration cannot introduce further conflicts. Other remains unlimited. Checks cover service rules, actual PostgreSQL trigger conflicts/restoration and HTTP duplicate rejection, preserving original fixture rows/files on rollback.

Schema-11 verification passed: 113 isolated Python tests, 19 browser scripts/13 frontend harnesses, all nine templates (59 routes), real PostgreSQL upload/classification/trigger/restoration conflict checks with rolled-back fixtures, and the read-only schema/file audit. Existing originals were retained; no native browser check, commit, push or deployment was performed.

## Office sign-in

Schema 12 installs the H space credential and retires all former sign-ins in one transaction. The PostgreSQL upgrade check used a temporary password inside a rolled-back transaction. It verified preserved actor identities, old-session revocation, the singleton constraint, password rotation and access to recovery and activity. The read-only audit checks the provisioned account and session foreign key after the local upgrade.
