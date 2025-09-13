from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.urls_autogen import module_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls.urls", namespace="core")),
]
urlpatterns += module_urlpatterns
if getattr(settings, "DEBUG", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler400 = "core.views.errors.error_400"
handler401 = "core.views.errors.error_401"
handler403 = "core.views.errors.error_403"
handler404 = "core.views.errors.error_404"
handler500 = "core.views.errors.error_500"
