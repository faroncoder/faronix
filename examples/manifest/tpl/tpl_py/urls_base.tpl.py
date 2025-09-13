# urls_base.tpl.py
from django.urls import path
from ..views.{{ view_name|lower }}_base import (
    {{ view_name }}ListView,
    {{ view_name }}CreateView,
    {{ view_name }}UpdateView,
    {{ view_name }}DeleteView,
)

app_name = "{{ app_label }}"

urlpatterns = [
    path("{{ view_name|lower }}/list",          {{ view_name }}ListView.as_view(),   name="{{ view_name|lower }}_list_htmx"),
    path("{{ view_name|lower }}/create",        {{ view_name }}CreateView.as_view(), name="{{ view_name|lower }}_create_htmx"),
    path("{{ view_name|lower }}/<int:pk>/edit", {{ view_name }}UpdateView.as_view(), name="{{ view_name|lower }}_edit_htmx"),
    path("{{ view_name|lower }}/<int:pk>/delete", {{ view_name }}DeleteView.as_view(), name="{{ view_name|lower }}_delete_htmx"),
]
