"""Jinja rendering and the unchanged static URL contract."""
from starlette.templating import Jinja2Templates
from limousine.config.runtime import ROOT
from .security import csrf_token, set_csrf_cookie, SESSION_COOKIE, valid_csrf

templates = Jinja2Templates(directory=str(ROOT / "src/limousine/presentation/web/templates"))
templates.env.globals["static"] = lambda name: "/static/" + name

def render_page(request, name, context=None, *, status_code=200, user=None):
    token = request.cookies.get("csrftoken", "")
    if not valid_csrf(request, token):
        token = csrf_token(request.app.state.settings, request.cookies.get(SESSION_COOKIE, ""))
    response = templates.TemplateResponse(request=request, name="web/" + name,
        context={"user": user, "csrf_token": token, **(context or {})}, status_code=status_code)
    set_csrf_cookie(response, token, request.app.state.settings)
    return response
