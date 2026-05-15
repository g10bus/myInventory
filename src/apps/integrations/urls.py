from django.urls import path

from .views.web import integrations_admin_view


urlpatterns = [
    path("integrations/manage/", integrations_admin_view, name="integrations-admin"),
]

