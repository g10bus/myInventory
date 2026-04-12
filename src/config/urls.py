from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.inventory.urls")),
    path("", include("apps.custody.urls")),
    path("", include("apps.accounts.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
