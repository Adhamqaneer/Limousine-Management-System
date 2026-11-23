# Frontend

Jinja HTML templates, CSS and plain JavaScript; no build step or npm runtime dependency. Start at templates/web/home.html and static/web/app.js for vehicle lookup/details.

| File | Responsibility |
| --- | --- |
| _header.html / _brand.html / _record_signature.html | Shared navigation and flat/3D office marks |
| app.css | Theme tokens, responsive layout and focus |
| app.js | Vehicle cards, forms, gallery actions and rename |
| appearance.js / page-tools.js | Before-paint preferences and shared controls |
| search.js / vehicle-filters.js | Fuzzy plate/type search and owner/model/type filters |
| ui-state.js | Unsaved detail drafts in page memory |
| drivers.js / driver-files.js | Period workflow and scoped documents |
| office-files.js / recycle-bin.js | Office documents and recovery |
| report-data.js / vehicle-report.js / vehicle-report.css | Selected fields, filtered results and printing |
| attachment-categories.js | Vehicle and driver attachment classification, plus the driver upload picker |
| attachment-download.js | Select document types and download the filtered vehicle originals as ZIP |
| attachment-scroll.js | Keep three attachment rows fully visible before a list scrolls |
| login.js / document_preview.js | Sign-in and local document preview |

English is default; Arabic sets RTL. Phones, plates and period dates use LTR isolation. Only language/theme persist in localStorage. Business records remain on the server; form drafts disappear on reload.

The Add vehicle form shows the vehicle type and plate rules under their inputs and validates each field as it is edited. An unfinished number is allowed while typing. On blur and before submission, the number must contain at least one hyphen between English digit groups. The edit form checks changed numbers when saving.

Add and edit show a localized message when the vehicle number is already in use. Vehicle creation and vehicle attachment dates display as DD/MM/YYYY in both languages, using Amman time.

Long lists use keyboard-focusable scroll regions. Attachment lists scroll from their fourth row and measure the first three rows so wrapped names and actions stay visible. Other lists use viewport-based height limits. Panel headings and actions sit outside the scroll regions. Leaving a vehicle restores the fleet scroll position, and changing search or filters brings the fleet results back to the top. Report previews use the same scrolling on screen and expand for print.

## Design

Follow the orange H SPACE [design reference](../design-system/h-space/MASTER.md). Light mode uses the daylight Camry scene; dark mode uses the night scene. Artwork is decorative, separate from uploaded card photos. Source PNGs are retained deliberately; served versions are lossless WebP. The [daylight prompt](daylight-artwork.md) records the source.

Cards use five columns from 1200px and fewer at smaller widths. Photos have 64x48 thumbnails and wrapping rows. Driver history/attachment panels have independent heights. Shared 3D headings mirror title/logo placement in RTL; actions sit beneath. Preserve 44px targets, visible focus, hints and reduced-motion support.

Template asset URLs include content versions to avoid stale scripts. WebP MIME is explicitly registered for Windows. Refresh after assets change; restart after Python changes.

Active navigation classes use a complete Jinja string expression so template formatters cannot merge nav-link and active. The navigation regression test renders all five destinations and checks the base layout class, active state and aria-current.

## Printing and previews

Reports use HTML tables and browser print/PDF. Letterhead mode adds the office banner/watermark; preprinted-paper mode omits them. Screen controls/decorative page headings are hidden in print. Driver periods have their own report. DOCX/XLSX previews are local bounded text/table conversions; original formatting/images/formulas may differ.

Vehicle reports start with no selected fields. The preview and print table use the order in which fields are checked, starting at the right edge in Arabic and the left edge in English. Rechecking a field places it last. Select all keeps the existing order and appends unchecked fields in the displayed order.

Attachment type choices load from the authenticated shared API. Vehicle Photos and Files upload to Other by default. Vehicle and driver attachment rows open the classification dialog, and driver uploads also offer a category picker. Office photos and files can be uploaded directly. The category download page has type checkboxes and one Download ZIP action, scoped to the current vehicle search and filters. It posts the selection with CSRF and saves the original-file archive. Categories are independent of filenames. Vehicle-data and driver-history reports use the browser's print/PDF workflow.

## Checks

Run node scripts/test_frontend.cjs for syntax and all dependency-free DOM harnesses. These cover lookup, filters, drafts/focus, upload/rename conflicts, recovery, driver periods, RTL labels and print gating. They do not establish visual browser, physical-phone or printer behavior; see [remaining work](next-steps.md).

The standalone category-management page and its links/script/styles were removed. The shared list and classification controls still work; no file metadata or category records were deleted.

Other now reveals an inline permanent-type field in the enlarged classification dialog. Names use the existing normalized-uniqueness guard; similar names require an explicit distinct-type confirmation. Upload category pickers can use the same dialog. Downloads asynchronously show a text-and-color availability matrix for every scoped vehicle and selected type, including zero-file vehicles. Stale preview responses are ignored; failed/pending/empty previews gate downloading. Plates retain LTR isolation in Arabic.
