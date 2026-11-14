from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from limousine.infrastructure.health import database_status


@require_GET
@ensure_csrf_cookie
def home(request):
    return render(request, "web/home.html")


@never_cache
@require_GET
def live(request):
    return JsonResponse({"status": "ok"})


@never_cache
@require_GET
def ready(request):
    status = database_status()
    return JsonResponse(
        {"status": "ok" if status == "ok" else "not_ready", "database": status},
        status=200 if status == "ok" else 503,
    )
