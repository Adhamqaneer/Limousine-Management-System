# Frontend

H SPACE retains an orange #ff641c, charcoal and white identity inspired by the owner's logo. The logo is redrawn as local SVG/HTML, not an exact raster copy. All assets and system fonts work locally.

The frontend uses Jinja2 templates with plain CSS/JavaScript. FastAPI serves source static assets directly. No bundler, npm, generated static build or external document viewer is required. English is the default; Arabic/RTL and light/dark preferences are supported. Browser preferences contain presentation settings only, never business records.

Login leads to searchable vehicle cards. Creation requires type and plate; details include driver name, chassis number and manufacture year. The card has its own cover upload, independent from the attachment gallery. Images/PDF/TXT open private preview routes. DOCX/XLSX use bounded local table/text extraction.

The ADMIN-only Team link opens user management. Members share vehicle access but cannot list/manage accounts. The owner account is protected. Members can be enabled, disabled, soft-deleted and restored; requests carry signed CSRF tokens. A restored account needs to sign in again.

Page templates are login.html, home.html, document_preview.html and users.html; _brand.html is shared. Scripts are app.js, login.js, document_preview.js and users.js; styling is app.css. Server-rendered identity data is escaped by Jinja2.

Template compilation and HTTP tests passed after the conversion. Prior Chrome visual checks covered the earlier H SPACE login/list/detail UI, language/theme controls and narrow windows. A fresh browser interaction check for the converted backend, actual phone testing and other browsers remain outstanding. See [README](../README.md).
