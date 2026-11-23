# Windows desktop preview

`desktop.py` opens the existing FastAPI interface in a pywebview EdgeChromium window. The launcher binds the HTTP listener to loopback and reserves a stable port for the profile so language and theme preferences persist. The website development entry point remains `manage.py runserver`.

The preview starts its own loopback PostgreSQL instance using the selected binaries. It generates credentials within the profile and creates a dedicated database and application role. The first-run screen uses a per-process setup token and session-bound CSRF, then applies the same database schema as the website. PostgreSQL stops on normal exit. A subsequent start reopens the same data and can recover an instance left by an abnormal exit.

The default development profile is `.local/desktop-preview/`. It contains the database, attachments, configuration and WebView profile. A second preview profile can be selected with `-Profile`. Keep these directories private. PostgreSQL and FastAPI listen only on the local computer.

The launcher passes `hspace-desktop.ico` to pywebview and sets the Windows taskbar identity to `HSPACE.DesktopPreview`. The icon uses the office wordmark at larger sizes and the existing H brand mark at small sizes. The multi-size icon was exported with Pillow. A Windows shortcut can use the same icon file.

The preview runs on the development computer. A distributable installer and installation testing on a clean Windows machine are deferred. An eventual installer should use the same application identity across releases and preserve the separate data directory on update or removal.

The Windows preview was opened and the first-run screen was checked in WebView2. A separate PostgreSQL smoke test verified an empty vehicle list, password setup, sign-in, a test vehicle and attachment, restart persistence, and clean shutdown. Native print and download dialogs still need an in-window check.
