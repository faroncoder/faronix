

# --- Only add new routes, do not overwrite existing ---
from django.urls import path
from . import views

app_name = "{{ app_label }}"

{% set single = (tabs|length == 1) %}
{% set route  = (view_slug or view_name|lower) %}

urlpatterns += [
    {% if single %}
    # Single-route: FBV for speed & simplicity
    path("{{ route }}/", views.{{ view_name|lower }}, name="{{ route }}"),
    {% else %}
    # Multi-route: CBV multiplexer (handles tabs via headers/partials)
    path("{{ route }}/", views.{{ view_name }}.as_view(), name="{{ route }}"),
    {% endif %}
]
