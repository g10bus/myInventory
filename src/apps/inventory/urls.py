from django.urls import path

from .views.web import my_assets_view


urlpatterns = [
    path("mytmc/", my_assets_view, name="mytmc"),
]
