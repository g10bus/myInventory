from django.urls import path

from .views.web import custody_admin_view, history_view, transfers_view


urlpatterns = [
    path("history/", history_view, name="history"),
    path("exchange/", transfers_view, name="exchange"),
    path("custody/manage/", custody_admin_view, name="custody-admin"),
]
