from django.urls import path
from .views import load_revcat_snippet
from .views import manifest_dashboard, load_manifest
from .views import diff_manifest_versions


urlpatterns = [
    path("revcat/snippet/", load_revcat_snippet, name="revcat-snippet"),
    path("manifest/", manifest_dashboard, name="manifest-dashboard"),
    path("manifest/load/<str:name>/", load_manifest, name="load-manifest"),
    path("manifest/diff/", diff_manifest_versions, name="manifest-diff"),

]
