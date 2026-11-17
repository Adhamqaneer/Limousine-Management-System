# H SPACE — Vehicle Management System

H SPACE is a local-first vehicle management website for a family car office. The backend uses **FastAPI on Uvicorn**, with PostgreSQL as its only runtime database. Cloud deployment is deferred while the application is tested locally.

The interface keeps the orange/charcoal identity, English by default, Arabic/RTL and light/dark mode. Vehicle cards open a detail view. Creating a vehicle requires its type and plate number; owner name/phone, driver name/phone, chassis number and vehicle model are optional text fields. Card photos are uploaded independently from gallery attachments.

## Interface and backgrounds

The H SPACE Studio refresh uses the owner's orange/charcoal logo identity and a locally generated **Toyota Camry** architectural background. Sign-in has a cinematic full-scene backdrop and an opaque, readable form; the vehicle list has a matching hero, with a calmer ambient background throughout the workspace. The image is decorative and is never assigned as a vehicle's uploaded card photo.

Navigation, cards, forms, Team and Office-document previews share the new visual system. English/Arabic RTL and both themes remain available on all pages; light mode uses warm-white data surfaces and a white sign-in panel against the cinematic scene. Sign-in includes a Show/Hide password control without changing authentication. Team provides retry feedback when loading fails.

The refresh changes presentation only: no database migration, new environment setting or dependency is required. The previous deletion feature still requires schema version 2. Existing data, attachments, account roles and APIs are unchanged. The public background asset is `static/web/hspace-camry-studio.png` (1672 × 941, approximately 1.7 MiB), generated for this project with imagegen and served locally. Shared header/icons and eight small browser scripts support the pages; there are no external fonts, video backgrounds or added UI frameworks.

The requested ui-ux-pro-max skill informed the accessibility/interaction review. Brand-matching rules and tokens are in [the design master](design-system/h-space/MASTER.md); implementation details are in [the frontend guide](docs/frontend.md).

The refresh passed 54 existing tests, page-template compilation, six JavaScript syntax checks and calculated contrast checks for the main text/action/control pairs. The loopback server served the new login, background and shared controls with HTTP 200. Browser access was unavailable; desktop/mobile rendered layouts and interactive visual checks at 375/768/1024/1440px remain unverified. The owned preview server was stopped after verification. After starting the project, use Ctrl+F5 to reload updated styles/scripts. Publishing the source does not deploy the application; cloud deployment remains deferred.

## Compact cards and interaction

The frontend-design refinement makes the vehicle grid fit **five cards at laptop viewport widths of 1200 CSS pixels and above**. It uses four columns at 1024–1199px, three at 800–1023px, two at 561–799px and one at 560px or below. Browser zoom changes the available CSS viewport width. Cards use smaller spacing and plate headings while keeping photo/removal controls at least 44px high; long text and footer actions wrap.

On a fine mouse pointer, cards lift slightly, tilt by at most 1.5 degrees per axis and show a soft orange highlight. Pointer movement is batched into one animation frame; tilt stops over action buttons and resets on leaving, scrolling, resizing, rerendering or hiding the page. Touch and keyboard access use native links/buttons, press feedback and visible focus. Nothing becomes accessible only on hover.

Buttons and focused fields provide clearer feedback; save buttons expose busy state and a spinner. Opening details or the add dialog has a short transition. Sign-in uses one coordinated entrance; no continuous background animation was added. Reduced-motion preferences suppress these effects, including changes made while a page is open. Decorative section numbers and the sign-in access index were replaced by meaningful icons/labels. Data, API and database behavior are unchanged.

Validation for this refinement: 14 focused health/vehicle HTTP tests, all seven JavaScript syntax checks and isolated interaction-controller checks passed. Controller checks covered frame batching, bounded tilt, touch exclusion, action-button stability, reset/cancellation and live reduced-motion changes. Native Windows Chrome review reached wide and narrow windows, English/Arabic and dark/light workspace views with existing data. The final narrow-heading adjustment remains visually unverified: Computer Use stopped when it could not reliably verify the browser URL. A full five-occupied-card row, exact viewport sizes, pointer animation appearance and physical phone testing remain outstanding. No sample inventory was added for the review. Reload the updated interface with Ctrl+F5. Source publication does not migrate local data or deploy the application.

## Approximate search and search focus

Vehicle search now ranks the already-loaded authenticated list in the browser using search.js. Unicode normalization, Arabic diacritics/tatweel removal, alef normalization, alif-maqsura matching, case folding and Arabic/Persian digit conversion apply only to comparison; saved vehicle data is unchanged. Every query word must match. Exact names come before partial and approximate name matches; ties keep the existing vehicle order. Names of four to seven characters allow one edit; longer words allow two, including adjacent transpositions. Short and numeric tokens are never typo-corrected. All-numeric plate queries support exact/substring matching with common spaces/dashes ignored, preserving digit order and leading zeros. Queries over 160 normalized characters return no results.

The search control now has one visible focus outline around the icon and input together. Its inner input does not draw a second outline; other form fields retain their focus indicators. Keyboard focus remains visible in both themes.

Validation: 17 frontend regression cases passed, covering Arabic/English spelling, normalization, transpositions, exact-first ranking, mixed queries, plate digits/order, empty queries and input bounds; source records were unchanged. Run them with optional Node.js via `node tests/test_search.cjs` (no npm packages). Application/template compilation passed. The focus appearance and end-to-end typing have not been freshly verified in a browser. No database migration, dependency or API change is required; these changes are not committed or pushed.

## Vehicle detail signature

The detail heading replaces the visible numeric record badge (for example #2) with an H SPACE office signature using the existing vector mark and wordmark. The title and signature share one aligned grid row between the record label and creation date. Static perspective, layered extrusion, a highlight and a soft cast shadow create the 3D treatment. The enlarged desktop signature occupies a 240–340px area, with a 74–94px mark and 44–56px wordmark. It scales down on tablets/phones while retaining its place beside the title; long names wrap and the Latin logo remains LTR in either interface language. Title alignment follows the interface language explicitly, independently of dir=auto on the vehicle name. There is no divider, extra caption or separate mobile logo row. The shared logo elsewhere is unchanged. Old record-ID DOM bindings were removed; database IDs and APIs are unchanged. No new raster asset, dependency or migration is required.

The signature is decorative and hidden from screen readers because office identity is already present in the shared header. The prior signature pass passed fourteen focused health/vehicle HTTP tests and app.js syntax checking. For the aligned 3D revision, template compilation and the focused HTTP tests passed. The earlier browser attempt was blocked by URL verification. After the size/alignment follow-up, native Windows Chrome inspection succeeded in English and Arabic, in wide and narrow windows, with the existing English-named vehicle. The mirrored layout, right alignment of Latin vehicle text in Arabic and enlarged 3D mark were visually confirmed without changing vehicle data. This covers browser windows, not a physical phone or exhaustive names/viewport sizes.

## Vehicle information fields

The detail form contains eight fixed fields in this order: owner name, owner phone, driver name, driver phone, vehicle type, vehicle model, chassis number and vehicle number. Creation still requires only type and vehicle number. All values remain text to preserve leading zeros. Vehicle model is the UI label for the existing manufacture_year column/API key; no new year range or four-digit restriction is imposed.

Owner/driver names and vehicle type accept English or Arabic letters, Arabic diacritics and spaces. Owner phone accepts ASCII, Arabic-Indic and Persian digits only. Driver phone and model accept ASCII digits (0–9) only. Chassis accepts ASCII letters, digits or both, preserving case, such as ABC, 00123 or JT001a; punctuation and Arabic characters are rejected. Vehicle numbers accept ASCII digit groups with optional hyphens between them, preserving formats such as 50-1746. No plus signs, embedded whitespace or automatic digit conversion are applied. Optional fields can be cleared. Limits are 200 characters for names, 32 for phones/model, 120 for type/chassis and 64 for vehicle number.

Domain validation is authoritative for creation/edits; vehicle-validation.js provides equivalent localized browser feedback without stripping pasted characters. The bilingual detail form uses text inputs, numeric keyboard hints where appropriate, associated format hints and the existing responsive grid. Only changed fields are patched, so historical values outside the new character rules remain visible and untouched when another field is edited. Changing a historical value requires the new format.

Schema version 3 adds owner_name, owner_phone and driver_phone as non-null text columns with empty defaults and database phone-character constraints. Existing columns/values are retained. Names and legacy-column character rules are enforced by the domain rather than retroactive SQL constraints. Infrastructure maps the three fields; the authenticated HTTP adapter serializes them and accepts them in create/PATCH requests. No dependency or environment changes are required. Run python manage.py migrate in the intended configured local environment before restarting an older checkout, then hard-refresh the browser. This local database has already been upgraded after a private backup.

Validation: 60 Python tests and 27 frontend validation cases passed, together with JavaScript syntax and template compilation checks. Real PostgreSQL checks verified version 3, repeat migration, all new fields, mixed-case/leading-zero chassis values, rejection of invalid chassis/phone input and rollback of the temporary fixture. Existing vehicle/account/file metadata and private file hashes were compared and preserved; the read-only database/file audit passed. A fresh rendered-browser check of this eight-field form and physical-phone testing remain outstanding. Source changes have not been committed or pushed.

## Print vehicle data

Open **Print data** in the signed-in navigation, or /reports/vehicles/. All four accounts can select any of the eight agreed fields; the vehicle number is selected initially. Select all and Clear selection are available. The preview includes every vehicle in creation order, one row per vehicle, and only the chosen columns in the agreed field order. Missing values display an em dash. Values are rendered as text, preserving Arabic, casing and leading zeros. Names use automatic text direction while number/chassis values retain LTR direction.

The report includes the office identity, vehicle count and the data-load timestamp in Asia/Amman. Refresh data reloads the current PostgreSQL-backed list; it clears an older preview if loading fails. Printing is disabled during loading, after an error, with no fields or with no vehicles. Print / Save PDF opens the browser's native dialog. Choose Save as PDF there; no server-generated PDF or external viewer is involved. Native printing uses white A4 pages: portrait for one to four selected fields, landscape for five to eight, with repeating column headers and row-break avoidance. Browser/printer settings can override paper/orientation and optional browser headers/footers. Large reports span pages. On narrow screens, wide previews scroll within the paper area.

This is presentation-only: an authenticated FastAPI page, report-data.js selection/projection helpers, vehicle-report.js UI and dedicated print CSS reuse the existing authenticated vehicle-list API and application/repository. No database migration, dependency, environment variable, saved business data or new write endpoint is added. Selections exist only in page memory. Shared navigation and translations also link to reports from Vehicles, Team and Office previews; compact navigation can wrap to accommodate the third link on narrow screens. The CLI check now compiles the report template too. Restart the server after pulling Python changes, then reload the browser.

Validation: all 63 Python tests passed, including report authentication, shared member/admin access, no-store responses and static assets. All 255 nonempty column combinations passed frontend regression checks; a dependency-free DOM harness verified selection/clear, RTL labels, literal text cells, leading zeros, print gating, empty/error states and expired-session redirection. Six affected JavaScript files passed syntax checks; all five page templates compiled. A read-only real PostgreSQL integration comparison confirmed all eight API field values and creation order, with vehicle rows unchanged. Run optional Node.js checks using node tests/test_report_data.cjs and node tests/test_report_ui.cjs.

Rendered desktop/mobile layouts, the native print preview, multipage output and a physical printer remain unverified: browser access was unavailable and native Chrome was minimized without a usable activation control. The temporary loopback review server was stopped. Test these in your browser before relying on printed reports; source is not committed, pushed or deployed.

## Vehicle list filters

A compact Filters disclosure beside search contains exactly three native dropdown filters: owner name, vehicle model and vehicle type. Choices come from nonempty values in the complete authenticated vehicle list, with whitespace trimmed and duplicate choices removed. They retain the original spelling, case and leading zeros; selection uses exact text matching. Each dropdown initially includes all values, and multiple selections intersect (AND). Existing approximate plate/type search further narrows the filtered list while keeping its ranking behavior.

The list shows the matching count and a Showing X of Y summary. Clear filters resets only these three selections and leaves search text intact. No matches offers guidance to change search or clear filters. Choices and labels survive language switches and list refreshes; a selected value that disappears remains selected so the result accurately shows no matches until cleared. Dropdowns are unavailable while vehicle data is loading or unavailable. Options are taken from the full list rather than narrowed by other selections. Vehicles with an empty owner/model remain visible when the corresponding filter is set to All.

vehicle-filters.js contains presentation-only option/selection helpers; app.js composes them with search.js and updates the existing card grid. Labeled controls follow the site's theme and responsive layout (three filters and reset on wide screens, two columns on tablets, one on narrow screens), with native keyboard behavior and visible focus. The choices are inside a compact disclosure, closed initially; Done, Escape or clicking outside closes it. All labels and result messages support English/Arabic RTL. Selections exist only in page memory; nothing is written to browser business storage or PostgreSQL. The navigation Print data link opens all vehicles; the separate Print results action carries the current filters/search into a matching-only report. No API, migration, dependency or environment change is needed. Reload with Ctrl+F5 after restarting your usual local server if necessary.

Validation: 64 Python tests passed, including a home-template check for exactly three filter dropdowns; all five page templates compiled. Sixteen frontend checks passed for each individual filter, combined selections, Arabic names, blank details, deduplication, leading zeros, search intersection and unchanged input records. Both affected scripts passed syntax checking. Optional Node command: node tests/test_vehicle_filters.cjs. The filter's rendered layout and native dropdown interactions have not received a fresh browser check. Phone access remains deferred and the development server stays on loopback.

## Compact filters and printing matching results

The main toolbar now has a small **Filters** disclosure beside search instead of an always-visible filter form. Its badge shows the number of selected facets. Open it to choose owner, model or type; results update immediately. Done, Escape and outside clicks close it. Clear filters retains search text. When an owner is selected, the result summary names that owner and shows the matching vehicle count; the same owner name can appear on multiple vehicle rows. Other filters/search may narrow that count further.

**Print results** opens the report for the current owner/model/type selections and search combined, including model-only (for example 2022), type-only, owner-only and mixed criteria. Then select any of the eight report columns as before. Criteria and the matching count appear on the printable paper. The existing Print data navigation still opens all vehicles, and filtered reports provide an explicit Print all vehicles link. Empty/invalid scopes cannot print.

Only selection criteria and search are transferred in a URL fragment, not vehicle records or files. The fragment remains client-side; the report fetches the authenticated current PostgreSQL-backed list and reuses vehicle-filters.js/search.js to reproduce membership and search order. It is a fresh matching-data view, not a frozen copy: concurrent changes can affect membership, and the load timestamp identifies the read. Unknown/duplicate/oversized scope parameters fail closed with no printable table. Nothing is written to persistent browser business storage.

The owner-name field now offers a native datalist of existing valid owner names, including on a directly opened vehicle detail page. Suggestions load through the existing authenticated list API, and failures leave the form usable. Choosing an existing name is optional; new names remain allowed under the agreed validation. Suggestions refresh after saving. This does not introduce owner IDs, automatically merge spelling variants or rewrite existing names; matching remains exact after trimming. Reuse a suggestion to keep an owner's vehicles grouped consistently.

Presentation changes affect home/report templates, app.js, vehicle-filters.js, vehicle-report.js and their styles. No database/schema migration, new HTTP endpoint, dependency or environment variable is required. All account permissions and loopback binding are unchanged; phone access remains deferred.

Validation: 64 Python tests passed, including compact filter markup, result-print entry and owner suggestion wiring. Frontend regressions passed for selection transfer and combined search, model-only/type-only/owner-only report results, explicit all-vehicle mode, Arabic criteria, malformed scopes, no printable fallback on invalid input and existing loading/error/RTL behavior. The three changed scripts passed syntax checks; all page templates compiled. Rendered popover/datalist behavior and native print output still require browser review; no fresh browser or physical-printer verification is claimed. Source changes remain uncommitted/unpushed. Reload with Ctrl+F5 after your usual local server restart.

## Office print letterhead and watermark

All generated vehicle reports now share the owner's reference-inspired office stationery: an orange top ribbon with an angled left corner, the H SPACE logo at the physical right, Arabic office name/services and English HORIZONTAL SPACE / Limo & Transportation identity. The identity stays bilingual in either UI language. No contract text, signatures, personal details or invented contact numbers from the reference were added.

The shared _print_letterhead.html partial sits in the report table's repeated thead, ahead of the report title, load timestamp, count, criteria and column labels. Its cell span follows the selected one-to-eight columns. Both all-vehicle reports and filtered-result reports use this same template. A large, pale H SPACE logo/wordmark appears behind the data, with fixed positioning in print for page repetition. Decorative vector geometry and the existing vector brand keep the stationery sharp without new raster assets or dependencies. Print rows use transparent backgrounds so the watermark remains subtle and visible.

The letterhead uses the existing 12mm A4 printable margins, not full-bleed paper edges; printer settings and unprintable areas still apply. Orange print color is requested with print-color-adjust. Native browser print/PDF settings ultimately control color, paper and repeated-header behavior. Uploaded original documents/PDFs remain unchanged: the stationery applies to reports generated by the site, not to printing a previously uploaded file.

Validation: the Python suite passes 65 tests, including authenticated report markup with the letterhead in the table head and a screen-reader-hidden watermark. Report interaction checks passed for dynamic one/eight-column header spans, filtering, RTL and existing print gating; JavaScript syntax and page-template compilation passed. Native browser print preview, repeated multipage output, watermark contrast on actual paper and physical printer output remain unverified. No database, API, dependency or setup changes are required; reload updated assets with Ctrl+F5.

## Edge-to-edge stationery and centered watermark

The latest print refinement removes the generated report title/date row from the paper. The office identity, vehicle count, chosen data columns and filtered-report criteria remain. Native browser-generated dates, titles, addresses and page numbers are separate: turn off **Headers and footers** under the browser's print settings (usually More settings). The report's English/Arabic print hint now explains this; page JavaScript cannot reliably switch that browser setting.

Both A4 orientations request zero page margins. The orange letterhead starts at the top edge and spans the page width; table content keeps a 12mm internal inset. Real edge-to-edge ink still requires a borderless-capable printer and suitable paper settings; otherwise the printer can leave or clip a narrow edge. Preview paper now follows portrait/landscape proportions.

The H SPACE watermark is larger, horizontal and centered at 50% of the sheet, with opacity increased from 0.055 to 0.085 for slightly clearer visibility. It stays behind readable data and uses fixed positioning in print. This revision supersedes the earlier rotated/45%-height watermark and outer 12mm page margins.

Validation: report interaction checks and JavaScript syntax passed; focused report HTTP tests, template compilation and README checks passed. This layout-only change adds no database, API or setup changes. Native print preview, multipage placement and physical borderless output remain unverified. Hard-refresh with Ctrl+F5 to load the new assets.

## Choose blank or preprinted paper

The report's Print / Save PDF button now opens a bilingual native dialog with two choices before the browser print dialog: **With letterhead** includes the office ribbon/identity and H SPACE watermark for blank paper/PDF; **Without letterhead** suppresses both for paper already printed with the office stationery. The preprinted option keeps the same empty header space, so the data does not overprint the existing office identity. Counts, chosen columns, filters and records remain identical in both modes. Cancel or Escape dismisses the chooser without printing.

The chosen paper mode is reflected in the preview and kept only for the current page. Clicking Print / Save PDF always offers both choices again. Native Ctrl+P uses the current preview mode (letterhead initially); it cannot be intercepted to await this chooser. The long paper/browser-settings instruction paragraph was removed from the interface at the owner's request; browser header/footer guidance remains in this guide.

This changes only the report template, presentation script and CSS; no API, migration, storage or dependency changes are needed. Validation passed for both mode selections, cancellation, unchanged data cells, disabled-print gating, existing filtering/RTL/error behavior, focused report HTTP tests, template compilation and JavaScript syntax. Rendered dialog focus, native print preview and actual preprinted-paper alignment remain unverified and depend on the real stationery/printer. Hard-refresh with Ctrl+F5.

## Recoverable deletion and administrator recovery

All four signed-in accounts can delete a vehicle card, gallery attachment or card photo after confirmation. These operations are now **soft deletion**, not physical file removal. Ordinary vehicle lists, filters, search, owner suggestions, reports and existing file/vehicle URLs exclude deleted items; deleted routes return 404. Deleting a vehicle hides its children through the parent state without changing each child's own deletion flag. Restoring that vehicle brings back children that were visible before the vehicle deletion; files independently deleted earlier remain in Deleted items.

Only Adham/ADMIN can open **Deleted items**, read the activity history or restore records. Recovery is authorized in both application use cases and HTTP dependencies, requires CSRF for writes, and cannot be enabled by a hidden button or a member's forged request. Restore a parent vehicle before restoring an independently deleted child. A previously removed/replaced card photo can be restored only after the current card photo is removed; recovery never overwrites a newer active cover. A restored item can be deleted again, with both cycles preserved in history.

New vehicle/file additions record their creator. Every new addition, deletion and restoration records the actor ID, username at that time, target label/type/vehicle, timestamp and replacement reason when applicable. Deleted items display creator/deleter names and times; activity loads 100 newest events at a time, with Load older activity. Existing records get no invented uploader identity; older card-photo creation times may also be unknown. Deletion/restore events begin with this version and cannot identify people who deleted files under earlier versions.

Schema version 4 adds created_by, is_deleted, deleted_at and deleted_by to vehicle, attachment and cover metadata; it adds hspace_activity and replaces the all-row unique cover association with a partial unique index for one active cover per vehicle. All older rows and file bytes remain preserved. User deletion, cover replacement and admin recovery serialize on the parent vehicle row, update state and append activity in one transaction. SQL retention triggers reject physical deletion of business rows and changes/removal of activity rows, including attempts from an older running application. The schema-owning database role can still change its schema: this is application activity history, not independently tamper-proof audit storage.

Private-file cleanup checks all metadata, including soft-deleted references. An unsuccessful upload is queued for a reference-aware cleanup check rather than blindly unlinked after an uncertain commit. If the database is unavailable even for queuing, bytes are retained and a generic warning is logged; the file audit can identify unreferenced files for later investigation. No automatic purge, retention deadline or storage quota is implemented, so retained files consume disk space. Already-open file transfers may finish. Keep database and media backups together.

Responsibilities: domain/recycling.py defines actor/restore rules; application/recycling.py owns the recovery contract and authorization; the PostgreSQL repository implements retained state/history/locking; HTTP adds authenticated vehicle DELETE and admin-only recycle-bin/activity/restore routes; recycle-bin.html/js provide translated recovery and history. Existing attachment/card-photo DELETE URLs now soft-delete. **Restart any running local server after upgrading**, then hard-refresh assets. No new dependency or environment variable is needed. The intended local database is already upgraded to schema 4 after a private backup. Cloud deployment and phone access remain deferred.

Validation: 69 isolated Python tests passed, including member deletion, denied member recovery/history, administrator recovery, CSRF, no-store responses and actor forwarding. Real PostgreSQL/FastAPI verification passed for version 4/idempotency, actor-attributed additions/deletions/restorations, hidden lists/downloads/edits, parent/child recovery, member denial, cover replacement/restore conflicts, reference-aware cleanup, retained bytes, SQL retention guards and complete fixture rollback. Existing vehicle/attachment/cover/account/session values and original media hashes were compared and preserved; the database/file audit passed. All thirteen browser scripts passed syntax checks. All six page templates compiled. A dependency-free recycle-bin DOM harness passed parent-first button gating, creator/deleter history, literal safe labels, older-event cursor pagination, CSRF restoration and Arabic rendering (optional command: node tests/test_recycle_ui.cjs). Rendered browser/device recovery flows remain unverified. These changes are not committed, pushed or deployed.

## Compact vehicle-card actions

Vehicle cards now finish with one compact row of two 44px icon buttons: a gallery icon adds/changes the independent card photo, and a trash icon soft-deletes the entire vehicle after confirmation. Long action captions and the separate Remove card photo action were removed from cards. Localized accessible names include the vehicle number, native title tooltips explain each icon, keyboard focus remains visible and busy state still disables actions. Existing card links, counts, gallery attachments and creation order are unchanged.

To keep older-cover recovery usable, Deleted items exposes a confirmed Remove current card photo action to the administrator only when a deleted cover has a currently active replacement and its parent is active. It soft-deletes that current cover through the existing authenticated/CSRF-protected route; then the admin can restore the older cover. The deleted-item read model now includes has_current_cover; there is no schema migration or new route.

Validation: seventeen focused vehicle/recovery HTTP tests passed, affected script syntax passed, and the recycle-bin DOM harness verified the current-photo action, endpoint/CSRF, refresh and translated controls. The real PostgreSQL recovery verifier passed again with existing rows and media hashes preserved. Rendered icon layout and physical-device interaction are not freshly verified. Reload assets with Ctrl+F5. If deletion returns 404/405 or fails after the schema upgrade, restart the old development server: the running process must load the new routes and soft-deletion code. The user's port-8000 process was observed to lack recycle-bin and vehicle DELETE routes; it was left for the user to restart.

## Driver periods, corrections and compact records

All four accounts can maintain **Driver history**. Current driver name/phone still appear among the eight vehicle fields, but are read-only in the ordinary details form. Use Change driver for a different driver: enter name, phone and an effective start date. The previous period closes on that handover date, a new period is created and the vehicle's cached current fields update in one transaction. Returning drivers get separate periods. Correct current driver fixes the existing period without creating a new employment period; old/new name, phone and start date, actor and recording time remain in immutable correction history. Both actions enforce the agreed Arabic/English name and ASCII phone rules.

Existing current values were seeded with unknown start dates, unknown historical creators and unknown original recording times; no past dates or people were invented. Correct an unknown start if you know it, or leave it unknown. Known start dates cannot be cleared, and starts cannot overlap a prior period or precede the current period when handing over. Periods are calendar dates: the prior period excludes the handover day, and the new driver includes it. Multiple changes on one day are recorded, but a date-specific lookup identifies the last applicable period rather than distinguishing times within that day. Start dates cannot be in the future (using the local server calendar). Changes take effect immediately; this is not a future-scheduling workflow.

Inside a vehicle, the row-based history shows names, phone snapshots and periods, with separate correction revisions. The global Driver history page searches names by literal case-insensitive substring, optionally scopes to a vehicle and/or working-on date, and lists vehicle numbers/types, periods and who recorded them. Unknown start dates are excluded from date-specific results because their start cannot be established. Vehicle deletion masks history in ordinary read/search/print routes, while recovery preserves and reveals it again. No individual history deletion or historical-period editing is provided.

Print results on Driver history prints the actual search/date results using six fixed history columns (name, phone, vehicle number/type, start and handover date). It reuses the office letterhead/watermark and offers both blank-paper and preprinted-paper modes. It is separate from the selectable eight-column current-vehicle report. The current-vehicle report still uses current driver values; use Driver history when you need earlier periods or phone numbers.

Schema version 5 adds hspace_driver_assignment and hspace_driver_change. A partial unique index permits one current period per vehicle. Driver mutations serialize on the active parent vehicle, validate boundaries and transact current fields with period/revision data. A database guard rejects direct current-driver overwrites that do not match the history state; ordinary vehicle PATCH rejects driver edits too. History rows cannot be physically deleted, and change events cannot be updated/deleted through ordinary SQL. Domain/drivers.py owns input/boundary rules, application/drivers.py owns the use cases/contract, infrastructure/drivers.py owns persistence and presentation adds authenticated driver routes, the detail actions and drivers.html/js.

Data entry is more compact: four columns on wide screens, two on tablets and one on narrow screens, with 44px controls, smaller padding and tighter labels/gaps. Driver fields explain their dedicated actions. Admin recovery and activity now display continuous rows with separators rather than boxed cards; English/Arabic and both themes remain supported. Sign-in sizing is unchanged.

Validation: 74 isolated Python tests passed. The real local verifier python scripts/verify_drivers.py backed up/upgraded the intended database, verified migration idempotency, preserved existing row values/media hashes, and tested unknown starts, member assignment/correction, immutable old phone snapshots/actor, day-boundary lookup, repeated drivers, literal search, rejection of overlapping dates/direct overwrites, deleted-parent masking and rollback-only fixtures. Sequences may advance after rollback. The database/file audit passed at schema 5 with matching current-driver caches. A dependency-free UI harness (node tests/test_driver_ui.cjs) passed assignment versus correction, CSRF, cache synchronization, name/date search, both print modes, Arabic headings and error gating. JavaScript syntax and seven-template compilation checks passed. Native rendered compact layouts, calendar/dialog behavior and actual driver-report printing remain unverified.

The local database is already upgraded with a private backup. Restart any running development server, then Ctrl+F5; an old process does not know the new driver routes. No dependency/environment change, cloud deployment or phone-network access was added. Earlier driver values already overwritten before this feature cannot be reconstructed automatically.

## Current local installation

PostgreSQL 18 hosts the project-owned database `limousine_local`, with restricted role `limousine_local_app`. Private connection settings are in ignored `.env`. Existing vehicle rows, attachment metadata, cover records and file bytes were preserved during the framework conversion.

Four fixed account slots are configured: Adham qaneer, AbdAlhameed qaneer, Abdullah qaneer and Ahmad qaneer. Their existing passwords were retained. Private local credentials are in `.local/accounts.txt`, excluded from Git and Docker. Adham has the ADMIN role; the other three have MEMBER. All have the same vehicle access. Only the admin can disable, soft-delete or restore member accounts through Team. The admin account cannot be disabled or deleted through this feature. No public registration is provided.

From PowerShell in this directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -Command runserver
```

Open <http://127.0.0.1:8000/>. Stop with Ctrl+C. The server binds to loopback; use `-Port 8001` if needed. Restart after Python changes and use Ctrl+F5 after static asset changes. A physical phone cannot access this loopback address remotely without separate network configuration.

## Authentication and account data

Users have UUID identifiers, username, password hash, a constrained ADMIN/MEMBER role, active status, `is_deleted` and `deleted_at`. First/last name and email columns are absent. The application uses a Python role enumeration and PostgreSQL CHECK constraints, rather than a native PostgreSQL enum type.

Authentication uses opaque server-side sessions, **not access/refresh JWTs**. Sessions last 12 hours from sign-in without sliding renewal. Only the SHA-256 token hash is stored in PostgreSQL. The browser cookie is HttpOnly and SameSite=Lax; production enables Secure cookies. Sign-out, password changes, deactivation and soft deletion revoke sessions. Old framework sessions were discarded; sign in again after the conversion.

Signed session-bound CSRF tokens protect state changes, including login/logout. Passwords use PBKDF2-SHA256. New passwords require at least eight characters, cannot be entirely numeric and cannot match another account's password. There is no login rate limiter yet.

To change one account, supply its slot and username; the command prompts privately for the password:

```powershell
.\.runtime\python\python.exe manage.py setoperator 1 "Adham qaneer"
```

This does not update the private credentials note automatically.

## Files and previews

Uploads remain private in `media/vehicles/`; PostgreSQL stores filenames, storage keys, byte sizes and vehicle associations. Gallery uploads never choose or replace a card photo. Files are limited to 10 MiB, with bounded image/document validation. Images, PDF and TXT can be viewed through authenticated preview routes. DOCX/XLSX receive bounded local text/table previews; these do not reproduce Office formatting. Unsupported formats are rejected. No third-party viewer receives documents.

Each gallery image and document has a Delete button with a confirmation for recoverable soft deletion. All four signed-in users can delete attachments. The card has compact gallery/change-photo and delete-vehicle icon buttons. Current card-photo removal, when needed to recover an older photo, is available to the admin on Deleted items; gallery files remain independent. Deletion requires CSRF protection and scopes the attachment to its vehicle. Deleted preview/download links return 404; repeating a deletion returns 404.

Soft deletion updates metadata and records an actor-attributed event in one PostgreSQL transaction; original file bytes remain on disk. Deleted items are inaccessible through ordinary preview/download routes. Only the administrator can restore them through Deleted items. An already-open download may finish. Historical permanent deletions from earlier versions cannot be reconstructed by this feature; retained backups remain separate.

Retry deferred file cleanup with `python manage.py cleanupfiles` (up to 100 entries per invocation). This processes only queued keys, preserves every still-referenced file (including soft-deleted records), and never scans/deletes unrelated uploads. No background worker is configured. The queue now handles unsuccessful/unreferenced uploads and older deferred cleanup; user deletion and card-photo replacement never enqueue retained bytes.

Vehicle deletion is recoverable as described below. Reservations, accounting and maintenance remain outside scope.

## Setup on a new machine

Use Python 3.12+ and PostgreSQL 14+. Dependencies are pinned in [requirements.txt](requirements.txt): FastAPI, Starlette, Pydantic, Uvicorn, Jinja2, python-multipart, psycopg, python-dotenv, Pillow and the HTTP test client. The frontend uses plain HTML/CSS/JavaScript and local assets, without npm or a build step.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe scripts/setup_local.py
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -Command runserver
```

Copy the example only when `.env` does not already exist. Setup privately prompts for the local PostgreSQL administrator password, provisions only the project database/role, writes application credentials locally, applies the schema and creates the four named accounts when none exist. Existing accounts are preserved. Never commit secrets or use this setup against another project's database.

Environment variables: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `HSPACE_SECRET_KEY`, `HSPACE_ALLOWED_HOSTS` and `HSPACE_ENV` (local or production). Production requires complete database settings, a strong secret and explicit allowed hosts. Private uploads, runtime, backups and generated artifacts are ignored.

## Database and architecture

In pgAdmin, refresh Databases, open **limousine_local → Schemas → public → Tables**. Right-click a table, then View/Edit Data → All Rows. The ten application tables are:

| Table | Responsibility |
| --- | --- |
| limo_vehicle | Agreed vehicle text fields and creation time |
| limo_attachment | Gallery/file metadata |
| limo_vehicle_cover | Independent card photo metadata |
| hspace_user | Four UUID accounts, role and soft-delete status |
| hspace_session | Hashed session tokens and expiry |
| hspace_schema_migration | Applied schema versions |
| hspace_file_cleanup | Deferred cleanup of unsuccessful/unreferenced files |
| hspace_activity | Actor-attributed additions, deletions and restorations |
| hspace_driver_assignment | Driver periods and phone snapshots per vehicle |
| hspace_driver_change | Immutable assignment/correction before-and-after history |

```sql
SELECT id, plate_number, vehicle_type, driver_name,
       chassis_number, manufacture_year, created_at
FROM public.limo_vehicle ORDER BY id;
```

The conversion removed Django source, configuration, packages and old authentication/framework tables, including the temporary legacy schema. Core vehicle table names and identifiers were preserved. Ignored emergency backups under `.local/backups/` contain pre-conversion snapshots; they are not used by the running app. Backup restoration has not been tested. The current migration command initializes only the FastAPI schema and is idempotent; it is not an importer for older installations.

Responsibilities remain separated: business rules in domain, use cases/contracts in application, PostgreSQL/files/passwords/schema in infrastructure, and HTTP/templates/assets in presentation. `manage.py` is a small project CLI, not a framework dependency. It supports runserver, check, test, migrate, cleanupfiles, setoperator and a compatibility collectstatic command (no build is needed). Local schema changes are restricted to the configured loopback `limousine_local` database; do not run migrations against an unintended environment.

Schema version 2 adds the cleanup queue and validates required vehicle fields, bounded positive file sizes, supported file kinds, safe unique storage keys and session hashes. It removes an inherited duplicate index and indexes session expiry. Upgrading an existing local database takes a private backup first; invalid historical rows stop the upgrade rather than being silently altered. The vehicle list now batches metadata reads into three queries instead of adding two queries per vehicle.

For an existing checkout, stop the development server, run `python manage.py migrate` in the configured environment, then restart it. The deletion feature and card-photo replacement need schema version 2. `manage.py cleanupfiles` is also available to retry deferred file removal.

Run `python scripts/check_database.py` for a read-only local audit of role privileges, expected schema versions/constraints/indexes, file references and byte sizes. It prints counts/findings without row contents or secrets. Run filesystem checks while uploads/deletions are idle. This does not establish production readiness. The local application role owns its schema for setup; separate migration/runtime roles and tested backup restoration remain production work.

## Verification

```powershell
.\.runtime\python\python.exe manage.py check
.\.runtime\python\python.exe manage.py test
.\.runtime\python\python.exe scripts/check_readme.py
git diff --check
```

The conversion passed 48 isolated tests and compiled all four page templates. Real local PostgreSQL integration checks passed for all four existing passwords, UUID/roles, admin-only account changes, soft deletion/restoration, session revocation/expiry, CSRF, vehicle creation/editing, independent card photos, image/PDF/TXT/DOCX/XLSX previews and private downloads. Test fixtures were removed. Existing business rows, password hashes and attachment bytes were compared before/after and preserved. Removal of the legacy schema and an idempotent schema rerun were also verified. A fresh Uvicorn process returned HTTP 200 for live health, real PostgreSQL readiness and the branded login page after cleanup; the project interpreter could no longer import the removed framework. The verification server was stopped afterward. All four JavaScript files passed syntax checks.

The earlier conversion-only scripts/verify_local.py is retired/guarded on schema 4 because its cleanup physically deleted fixtures. Use the current recovery verifier instead; it does not change real account statuses or sessions.

Run `python scripts/verify_recycling.py` for opt-in real local recovery verification (scripts/verify_deletion.py delegates to it for compatibility). It backs up/upgrades the intended local database if needed, verifies idempotency and compares existing rows/files, then exercises recovery/actor history with temporary files and rollback-only database fixtures. Sequence numbers can advance despite fixture rollback. Run while the application is idle.

This addition passed 54 isolated tests and real PostgreSQL deletion checks, including member permissions, authentication/CSRF, wrong-vehicle rejection, repeated deletion, cover/gallery independence, replacement cleanup, rollback on a database error, disk failure/retry and actual CHECK, foreign-key and unique-storage-key constraints. Existing account/business rows and original file hashes remained unchanged. The final read-only audit found one existing vehicle, seven attachments, one cover, four users, zero pending cleanups, no missing/mismatched/unreferenced files and no missing expected constraints/indexes; the role has no superuser, create-database, create-role, replication or bypass-RLS privileges. Version 2 was applied successfully after a private backup, and rerunning the migration completed without reapplying the upgrade.

All four JavaScript files passed syntax checks. A fresh visual browser check was attempted but the computer-use safeguard stopped it because it could not establish the active Windows browser URL reliably; the updated controls/confirmation and narrow layout have not been visually verified. The loopback preview server was stopped afterward. Backup restore, restart, Docker and production checks remain outstanding. Cloud deployment remains deferred.

The test client currently emits an upstream deprecation warning about httpx; tests still pass. Browser appearance was checked on the previous UI version; the migrated backend has not yet received a fresh browser interaction check. Docker, backup restoration, device restart and deployment remain unverified.

CI runs the README change check, application/template check and isolated tests. It does not connect to the real local database. Documentation checking verifies that README changed, not that every statement is correct.

Docker/Compose supplies only the web service, binds its host port to loopback and uses a persistent media volume. A container needs separately configured PostgreSQL connectivity; its localhost is not the host computer. Production still needs HTTPS, rate limiting, operational hardening and tested database-plus-media backups.

## GitHub and local data

The repository contains application source, tests, documentation and setup examples. The README and supporting guides are maintained in English; the application's Arabic interface remains available.

Local connection secrets, account credentials, uploaded files, database backups, wallet files and the local Python runtime are excluded from Git. Checkout-local design skills under .agents/ and their skills-lock.json are also excluded; they are authoring tools and are not required to run the application. Cloning or pulling the repository does not restore the local database or attachments. Set up a private environment separately using the steps above. Pushing source to GitHub does not deploy the application or move local data to the cloud.

See [architecture](docs/architecture.md), [frontend](docs/frontend.md) and [remaining work](docs/next-steps.md).

Driver-report refinement: the Recorded by column was removed from the global history preview and printed report in both languages. The letterhead spans six columns; internal creator/correction records and the per-vehicle history remain unchanged. The existing driver UI regression harness and script syntax checks passed; no database change is required. Native print appearance was not freshly reviewed.
