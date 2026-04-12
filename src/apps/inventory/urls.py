from django.urls import path

from .views.web import asset_admin_view, asset_create_view, asset_edit_view, my_assets_view


urlpatterns = [
    path("mytmc/", my_assets_view, name="mytmc"),
    path("assets/manage/", asset_admin_view, name="asset-admin"),
    path("assets/manage/create/", asset_create_view, name="asset-create"),
    path("assets/manage/<int:asset_id>/", asset_edit_view, name="asset-edit"),
]
