# H SPACE Studio — Design Master

## Direction and sources

Use the owner's orange/charcoal H SPACE identity and the requested Toyota Camry scene. This is a private vehicle workspace, not a marketing landing page. Keep the existing vehicle list/detail model and English default, Arabic/RTL and light/dark modes.

The ui-ux-pro-max design-system searches were reviewed. Their full palette/typography/pattern output was not accepted: it did not match the supplied brand and internal-product scope. This master is a manually adapted system based on the owner's reference and the skill's general guidance, with a verified focused UX match for background text contrast. It does not preserve unverified catalog recommendations.

## Background and composition

- Asset: src/limousine/presentation/web/static/web/hspace-camry-studio.webp; lossless, pixel-identical conversion of the retained source PNG.
- AI-generated graphite Toyota Camry, orange portal/curved road, dark architectural studio.
- Sign-in uses a full scene, calm form area and strong story hierarchy. Mirroring is presentational CSS only.
- Interior uses a cinematic list hero and a subdued ambient background beneath opaque data surfaces.
- The artwork is decorative. Never use it as the vehicle's uploaded card photo or as evidence of actual inventory.
- Keep information readable when artwork fails to load; solid color and scrim fallbacks remain.
- No looping video, ornamental particle animation or scroll-driven effects.

## Tokens

| Role | Dark | Light |
| --- | --- | --- |
| Page | #101113 | #f5f3ef |
| Surface | #1a1c20 | #ffffff |
| Text | #f5f5f3 | #202329 |
| Muted text | #b0b3ba | #62676f |
| Brand/action fill | #ff641c | #ff641c |
| Action text | #231007 | #231007 |
| Accent text | #ff965f | #ac3d0c |
| Control boundary | #69717c | #858b94 |

Normal checked text pairs exceed 4.5:1; checked input boundaries exceed 3:1. Composed-image text still needs browser review. Hero/story text uses dedicated light colors over dark scrims, independent of page theme.

## Typography, spacing and interaction

Use local Bahnschrift/Segoe UI for display and Segoe UI/Tahoma/Arial for UI, with no external font dependency. Base text is 16px; form inputs are 16px on small screens. Use a 4/8px spacing rhythm, 44px minimum controls, 20–24px main radii, 10–12px control radii and 180ms state transitions.

Vehicle lookup takes priority over the cinematic banner: search/filters precede it and its minimum height is 190px on desktop, 170px on tablets and 140px on phones, growing with content. Compact detail hints use 13px. Mobile filter fields stack in one column. Destructive card controls use the error token at rest, a distinct border and extra separation from gallery actions. Numeric plate-match highlighting keeps LTR isolation and the primary/primary-text contrast pair. Keyboard focus survives card replacement/removal and returning from a detail view.

Favor short, visible primary actions. Wrap names and filenames; never put essential actions behind hover. Keep keyboard focus visible and preserve native form/dialog semantics. Respect prefers-reduced-motion. The Show/Hide password control keeps autocomplete and paste available.

## Layout and maintenance

Shared header/icons/brand apply across all pages. Main navigation has only real destinations. Team is ADMIN-only. There are no invented metrics, statuses or extra vehicle fields.

Laptop viewports at least 1200 CSS pixels wide show five compact vehicle columns; 1024–1199 use four, 800–1023 use three, 561–799 use two, and smaller widths use one. Large screens retain a split sign-in view. Smaller widths collapse the grid and header/navigation; mobile sign-in stacks story and form. Target review widths: 375/768/1024/1440px and both orientations.

The frontend-design refinement uses deliberate action-driven motion: fine-pointer lift/tilt and an orange highlight for vehicle links, stable upload/removal targets, clear keyboard focus, native touch press feedback, short details/dialog opening and one sign-in entrance. Reduced motion disables effects. Decorative sequence markers are removed.

Wide/narrow native Windows Chrome and English/Arabic dark/light views were reviewed with existing data. Browser access stopped before rechecking the final narrow-heading correction. Exact viewport/device testing, a full five-occupied-card row and pointer animation appearance remain unverified. README records actual checks.
