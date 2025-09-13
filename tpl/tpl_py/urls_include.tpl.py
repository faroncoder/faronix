{# urls_include.tpl.py #}
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    {% for spec in active_specs %}
    # {{ spec.view_name }} module
    path("{{ spec.view_slug }}/", include("{{ spec.app_label }}.urls.{{ spec.view_slug }}_urls", namespace="{{ spec.view_slug }}")),
    {% endfor %}
]
