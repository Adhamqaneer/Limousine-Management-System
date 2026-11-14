from django.urls import path

from . import vehicle_views, views

app_name = "web"
urlpatterns = [
    path("", views.home, name="home"),
    path("api/vehicles/", vehicle_views.vehicles, name="vehicles"),
    path("api/vehicles/<int:vehicle_id>/", vehicle_views.vehicle_detail, name="vehicle_detail"),
    path("api/vehicles/<int:vehicle_id>/attachments/", vehicle_views.attachments, name="attachments"),
    path("api/vehicles/<int:vehicle_id>/attachments/<int:attachment_id>/download/", vehicle_views.attachment_download, name="attachment_download"),
    path("api/vehicles/<int:vehicle_id>/attachments/<int:attachment_id>/preview/", vehicle_views.attachment_preview, name="attachment_preview"),
    path("health/live/", views.live, name="live"),
    path("health/ready/", views.ready, name="ready"),
]
