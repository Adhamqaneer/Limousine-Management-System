"""Jinja rendering and versioned local assets for coherent page updates."""

from functools import lru_cache
from hashlib import sha256

from starlette.templating import Jinja2Templates

from limousine.config.runtime import ROOT

from .security import SESSION_COOKIE, csrf_token, set_csrf_cookie, valid_csrf

templates = Jinja2Templates(directory=str(ROOT / "src/limousine/presentation/web/templates"))
STATIC_ROOT = ROOT / "src/limousine/presentation/web/static"


@lru_cache(maxsize=128)
def _asset_version(path, modified_ns, size):
    # Stat values invalidate the digest cache after an edit, even without restart.
    return sha256(path.read_bytes()).hexdigest()[:16]


def static_url(name):
    path = STATIC_ROOT / name
    stat = path.stat()
    return "/static/" + name + "?v=" + _asset_version(path, stat.st_mtime_ns, stat.st_size)


templates.env.globals["static"] = static_url


def render_page(request, name, context=None, *, status_code=200, user=None):
    token = request.cookies.get("csrftoken", "")
    if not valid_csrf(request, token):
        token = csrf_token(request.app.state.settings, request.cookies.get(SESSION_COOKIE, ""))
    response = templates.TemplateResponse(
        request=request,
        name="web/" + name,
        context={"user": user, "csrf_token": token, **(context or {})},
        status_code=status_code,
    )
    set_csrf_cookie(response, token, request.app.state.settings)
    return response
