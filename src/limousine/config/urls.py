from django.urls import include, path

urlpatterns = [path("", include("limousine.presentation.web.urls"))]
