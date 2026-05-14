from django.urls import path

from .views.web import org_admin_view


urlpatterns = [
    path("org/manage/", org_admin_view, name="org-admin"),
]
