from django.urls import path

from apps.core.views import live, ready

from .views.web import home_view, root_redirect


urlpatterns = [
    path("", root_redirect, name="root"),
    path("home/", home_view, name="home"),
    path("health/live/", live, name="health-live"),
    path("health/ready/", ready, name="health-ready"),
]




