from django.urls import path

from .views.web import custody_admin_view, history_pdf_view, history_view, transfer_report_pdf_view, transfers_view


urlpatterns = [
    path("history/", history_view, name="history"),
    path("history/pdf/", history_pdf_view, name="history-pdf"),
    path("exchange/", transfers_view, name="exchange"),
    path("exchange/transfers/<int:transfer_id>/pdf/", transfer_report_pdf_view, name="transfer-report-pdf"),
    path("custody/manage/", custody_admin_view, name="custody-admin"),
]
