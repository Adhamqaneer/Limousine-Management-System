# Vehicle interface

The interface is a simple vehicle list and a separate detail view. The former 3D showroom is removed. English is the default language; Arabic/RTL and light/dark preferences remain available and use localStorage only for appearance preferences, never business records.

## Presentation files

- `templates/web/home.html`: page structure, vehicle grid, fixed-field forms and attachment sections.
- `static/web/app.css`: styles, responsive layout, light/dark tokens and RTL adjustments.
- `static/web/appearance.js`: restores the palette before stylesheet loading.
- `static/web/app.js`: translation, page navigation, rendering and API interactions. Business rules and persistence belong to Python layers.
- `vehicle_views.py`: HTTP adaptation and response serialization for the vehicle application service.

Paths are relative to `src/limousine/presentation/web/`.

## Behavior

New vehicles appear after existing vehicles in order of addition. The plate number is the only fixed field currently agreed; more fields can be added through the domain, application, ORM migration and form. It remains text so leading zeroes and different plate formats are preserved.

Each vehicle has its own photo gallery and file list. The first image is used as the vehicle card cover. Uploads are checked by extension, content and size (10 MiB per file). Raster photos are verified and decoded using Pillow, with a 25-million-pixel cap; malformed or truncated images are rejected before storage. Documents download as attachments; only supported raster formats have inline previews. Metadata uses Oracle; file bytes currently use the local `media/` directory. Object Storage is future work.

Without Oracle configuration, the page and add-form preview remain available with a clear storage notice; saving is disabled. No browser-local substitute database or runtime fake repository is used.

Existing form/upload/detail messages are stored as translation keys so they switch language with the interface. Navigation focuses the destination heading; language changes and attachment refreshes preserve focus.

## Verification limits

Python tests cover validation, addition order, editing, attachment ownership, uploads, image decoding, error handling, CSRF and README enforcement using isolated test doubles and temporary Git repositories. Frontend message translation and focus changes were exercised with DOM/fetch stubs, not a real browser. ORM model/migration consistency is checked without connecting to Oracle. Real Oracle migration and persistence have not been verified. Browser QA of this replacement interface was blocked by the computer-use tool's inability to verify the current browser URL on Windows; previous showroom screenshots do not validate this interface.
