"""Start the H SPACE desktop application on Windows."""

import argparse
import ctypes
import os
import secrets
import socket
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Thread

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent / "src"),
)


@contextmanager
def profile_lock(profile):
    import msvcrt

    profile.mkdir(
        parents=True,
        exist_ok=True,
    )
    with (profile / "desktop.lock").open("a+b") as lock:
        try:
            msvcrt.locking(
                lock.fileno(),
                msvcrt.LK_NBLCK,
                1,
            )
        except OSError:
            raise RuntimeError("H SPACE is already open for this profile.") from None
        yield
        # Windows releases the lock when the file is closed.


@contextmanager
def local_web_server(
    app,
    profile,
):
    import uvicorn

    port_file = profile / "desktop-port.txt"
    port = int(port_file.read_text(encoding="ascii")) if port_file.exists() else 0
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as listener:
        listener.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_EXCLUSIVEADDRUSE,
            1,
        )
        try:
            listener.bind(("127.0.0.1", port))
        except OSError:
            raise RuntimeError("The H SPACE desktop port is already in use.") from None
        listener.listen()
        bound_port = listener.getsockname()[1]
        if not port:
            port_file.write_text(
                str(bound_port),
                encoding="ascii",
            )

        config = uvicorn.Config(
            app,
            log_config=None,
            log_level="critical",
            access_log=False,
            timeout_graceful_shutdown=10,
        )
        server = uvicorn.Server(config)
        thread = Thread(
            target=server.run,
            kwargs={"sockets": [listener]},
            daemon=True,
        )
        thread.start()
        try:
            started = time.monotonic()
            while not server.started:
                if (
                    not thread.is_alive()
                    or time.monotonic() - started > 15
                ):
                    raise RuntimeError("Could not start the H SPACE local web server.")
                time.sleep(0.05)
            yield f"http://127.0.0.1:{bound_port}"
        finally:
            server.should_exit = True
            thread.join(timeout=15)


def open_window(
    url,
    profile,
):
    import webview
    from webview.menu import Menu, MenuAction

    # Give the preview its own Windows taskbar identity when launched through Python.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("HSPACE.DesktopPreview")
    icon = (
        Path(__file__).resolve().parent
        / "src/limousine/presentation/web/static/web/hspace-desktop.ico"
    )

    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["ALLOW_FILE_URLS"] = False
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False

    window = webview.create_window(
        "H SPACE",
        url,
        width=1320,
        height=850,
        min_size=(760, 620),
    )
    menu = [
        Menu(
            "H SPACE",
            [
                MenuAction(
                    "Back",
                    lambda: window.evaluate_js("history.back()"),
                ),
                MenuAction(
                    "Back to H SPACE",
                    lambda: window.load_url(url.split("/desktop/")[0]),
                ),
            ],
        )
    ]
    webview.start(
        gui="edgechromium",
        private_mode=False,
        storage_path=str(profile / "webview"),
        menu=menu,
        icon=str(icon),
    )


def main():
    if sys.platform != "win32":
        raise RuntimeError("The H SPACE desktop application requires Windows.")

    from limousine.infrastructure.database import Database
    from limousine.infrastructure.desktop_postgres import DesktopPostgres
    from limousine.infrastructure.migrations import migrate, needs_operator_setup
    from limousine.presentation.web.factory import create_app

    parser = argparse.ArgumentParser(description=__doc__)
    default_profile = Path(os.environ["LOCALAPPDATA"]) / "H SPACE" / "Desktop Preview"
    parser.add_argument(
        "--profile",
        type=Path,
        default=default_profile,
    )
    parser.add_argument(
        "--postgres",
        type=Path,
        required=True,
        help="PostgreSQL bin directory",
    )
    arguments = parser.parse_args()
    profile = arguments.profile.resolve()
    postgres = DesktopPostgres(
        arguments.postgres.resolve(),
        profile,
    )
    with profile_lock(profile), postgres.running() as settings:
        database = Database(settings)
        setup_token = None
        if needs_operator_setup(database):
            setup_token = secrets.token_urlsafe(32)
        else:
            migrate(database)

        app = create_app(
            settings,
            setup_token=setup_token,
        )
        with local_web_server(
            app,
            profile,
        ) as origin:
            url = origin
            if setup_token:
                url += "/desktop/setup/?token=" + setup_token
            open_window(
                url,
                profile,
            )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        message = "H SPACE could not start. (" + type(error).__name__ + ")"
        if isinstance(
            error,
            RuntimeError,
        ):
            message = str(error)
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(
                None,
                message,
                "H SPACE",
                0x10,
            )
        else:
            print(
                message,
                file=sys.stderr,
            )
        raise SystemExit(1) from None
