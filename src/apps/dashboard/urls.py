from django.urls import path

from apps.core.views import live, ready

from .views.web import analytics_view, home_view, root_redirect


urlpatterns = [
    path("", root_redirect, name="root"),
    path("home/", home_view, name="home"),
    path("analytics/", analytics_view, name="analytics"),
    path("health/live/", live, name="health-live"),
    path("health/ready/", ready, name="health-ready"),
]




