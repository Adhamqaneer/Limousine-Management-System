# Remaining work

The current scope is a local FastAPI/PostgreSQL trial with four accounts. Adham is ADMIN; the other three share vehicle permissions. The framework conversion, account/session behavior, private files and core vehicle workflows passed isolated and real database integration checks. Old framework source/packages/tables were removed; business rows, file bytes and password hashes were preserved.

Attachment/card-photo deletion now retains metadata/bytes with confirmation, vehicle-scoped authenticated CSRF-protected routes and admin recovery. Version 2 strengthens actual file metadata constraints and indexes; scripts/check_database.py audits the local database/files without writes. See README for completed validation. The retry command is manual; background cleanup scheduling remains deferred.

The H SPACE Studio redesign now includes the requested Camry scene on sign-in/interior backgrounds, shared navigation, both themes/languages and accessible password visibility. Automated/template/static-resource checks passed; browser access was unavailable.

Before wider use, perform a fresh browser check of the converted backend, including the Studio backgrounds, Show/Hide password, Team, language/theme, narrow layout, deletion and document previews. The compact-card interaction refinement now uses five columns from 1200 CSS pixels, with fewer columns on narrower screens. Native Chrome review covered wide/narrow windows and language/theme controls, but the browser URL safeguard stopped further input. Recheck the final narrow-heading correction, pointer appearance and a full five-occupied-card row. Check 375/768/1024/1280/1366/1440px, landscape and reduced motion. Test a physical phone separately; development currently stays on loopback. Also test PostgreSQL/device restart and restoration of database plus media backups. Separate runtime and migration database roles before production.

Cloud deployment is deferred. It will need explicit database/file destinations, HTTPS, secrets, login rate limiting, operational monitoring, persistent storage and tested backups. Docker has been updated but not built or run. Existing local data will not move automatically. Backup scheduling remains future work.

Reservations, accounting and maintenance remain outside scope. Actual validation and setup commands are in [README](../README.md).

Verify the new approximate name search with actual office names, mixed Arabic/English queries and strict plate queries in the browser. Check the single search focus outline using mouse and Tab in both themes and RTL. Frontend regression cases passed; larger-dataset performance and end-to-end browser behavior remain to be assessed.

Visually review the new vehicle-detail office signature at phone/tablet/laptop widths, including RTL, both themes and long vehicle names. The visible numeric badge is removed; persistence IDs remain unchanged.

The detail signature was revised to static 3D styling aligned alongside the vehicle title in both layout directions. Browser URL verification blocked the requested Arabic/English visual checks; verify those layouts and phone/tablet fit before treating the revision as visually approved.

The enlarged 3D detail signature and mixed-script alignment fix were visually confirmed in native Chrome in Arabic/English, wide/narrow windows. Earlier URL-verification blocks were resolved for this check. Physical phones, exact breakpoint coverage and unusually long names still need review.

The owner subsequently authorized eight vehicle fields: owner/driver names and phones, type, model, chassis and vehicle number. Schema 3 is applied locally, with preserved existing rows/files and passing PostgreSQL/audit checks. Review the new form in both languages/themes on laptop and phone, including leading zeros, mixed alphanumeric chassis, paste errors and unchanged historical formats. Cloud migration remains deferred.

Print data is implemented for all eight fields and all existing vehicles, with 63 passing Python tests, exhaustive column-combination checks and DOM interaction checks. Before relying on output, check native print preview in Arabic/English for one, four, five and eight columns; test multipage repetition, long names/chassis, A4 settings and Save as PDF. Browser review was blocked by unavailable browser access/minimized native Chrome. No migration or cloud deployment is needed for reporting.

Three main-list filters (owner/model/type) now pass 16 frontend regression checks and the 64-test Python suite. Review native dropdowns and result counts in English/Arabic and both themes, including combined filters/search, clear, reload and a selected value no longer present. Phone access remains deferred at the owner’s request; keep loopback binding.

Compact filter disclosure, Print results for every owner/model/type/search combination and optional existing-owner suggestions are implemented. The report now supports either all vehicles or a fresh matching subset, and prints its criteria. Verify rendered keyboard dismissal, native datalist selection, Arabic/English criteria layout and multipage native printing when browser access is available. Exact-name grouping remains in use; no automatic owner-name merge or master-owner table is added.

Office letterhead and pale H SPACE watermark are implemented for generated reports. Verify their repetition on a multipage report in portrait/landscape, both interface languages and print-to-PDF; inspect watermark readability with background graphics enabled/disabled and on a physical printer. Current output uses 12mm printable margins rather than full bleed. Uploaded originals keep their existing content.

Check the latest zero-margin print stationery with browser Headers and footers disabled. Confirm the ribbon reaches the top, the larger horizontal watermark is centered and readable, and data stays inset in portrait/landscape. Borderless physical output depends on printer hardware/settings; no fresh native print verification is claimed.

Test both paper choices in the new print-style dialog: blank paper/PDF with stationery, and preprinted paper with no new letterhead/watermark but reserved header space. Confirm alignment against actual office stationery before printing a batch. Cancel, disabled-print cases and data preservation passed isolated checks; physical/native output is outstanding.

Recoverable deletion for all accounts and admin-only recovery/history are implemented; schema 4 was applied with a private backup. 69 isolated tests, rollback-only real PostgreSQL/API recovery checks and database/file audit passed with preserved existing rows/files. Check the rendered Deleted items/history page and repeated delete/restore interactions in both languages/themes. Decide storage capacity/retention/purge separately; no purge is implemented. Prior permanent deletions have no reconstructed records, actors or bytes. The legacy conversion verifier refuses schema 4, and verify_deletion.py delegates to verify_recycling.py.

Review the compact gallery/trash icon row on occupied cards in both themes/languages. Verify the admin current-photo action before older-cover recovery. The old development process on port 8000 lacked the new recovery/DELETE routes; restart it after source changes before testing deletion. No server process was changed in this follow-up.

Driver history and corrections are implemented at schema 5, with 74 isolated tests, rollback-only PostgreSQL/API verification and a driver UI harness. Review handover-day date semantics, unknown starts, returning drivers, correction revisions, both print modes and the compact form/admin record layouts in a real browser. Earlier overwritten driver identities are not reconstructed. Restart the development server after this update; no network/phone configuration is added.
