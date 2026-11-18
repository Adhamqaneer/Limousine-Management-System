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
| office-files.js / recycle-bin.js / users.js | Office documents, recovery and accounts |
| report-data.js / vehicle-report.js / vehicle-report.css | Selected fields, filtered results and printing |
| login.js / document_preview.js | Sign-in and local document preview |

English is default; Arabic sets RTL. Phones, plates and period dates use LTR isolation. Only language/theme persist in localStorage. Business records remain on the server; form drafts disappear on reload.

## Design

Follow the orange H SPACE [design reference](../design-system/h-space/MASTER.md). Light mode uses the daylight Camry scene; dark mode uses the night scene. Artwork is decorative, separate from uploaded card photos. Source PNGs are retained deliberately; served versions are lossless WebP. The [daylight prompt](daylight-artwork.md) records the source.

Cards use five columns from 1200px and fewer at smaller widths. Photos have 64x48 thumbnails and wrapping rows. Driver history/attachment panels have independent heights. Shared 3D headings mirror title/logo placement in RTL; actions sit beneath. Preserve 44px targets, visible focus, hints and reduced-motion support.

Template asset URLs include content versions to avoid stale scripts. WebP MIME is explicitly registered for Windows. Refresh after assets change; restart after Python changes.

Active navigation classes use a complete Jinja string expression so template formatters cannot merge nav-link and active. The navigation regression test renders all six destinations and checks the base layout class, active state and aria-current.

## Printing and previews

Reports use HTML tables and browser print/PDF. Letterhead mode adds the office banner/watermark; preprinted-paper mode omits them. Screen controls/decorative page headings are hidden in print. Driver periods have their own report. DOCX/XLSX previews are local bounded text/table conversions; original formatting/images/formulas may differ.

## Checks

Run node scripts/test_frontend.cjs for syntax and all dependency-free DOM harnesses. These cover lookup, filters, drafts/focus, upload/rename conflicts, recovery, driver periods, RTL labels and print gating. They do not establish visual browser, physical-phone or printer behavior; see [remaining work](next-steps.md).
