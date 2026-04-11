from django.urls import path

from .views.web import history_view, transfers_view


urlpatterns = [
    path("history/", history_view, name="history"),
    path("exchange/", transfers_view, name="exchange"),
]
