# views_base.tpl.py
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.http import HttpResponse
from .hx_helpers import trigger
from django.core.paginator import Paginator, EmptyPage
from ..models import {{ model }}
from .repo import {{ model }}Repo

from django.core.paginator import Paginator, EmptyPage

class {{ view_name }}ListView(View):
    template_name = "{{ view_name|lower }}_table.html"   # wrapper renders table + pager

    def get(self, request):
        # page inputs
        try:
            page      = int(request.GET.get("page", "1"))
        except ValueError:
            page = 1
        try:
            page_size = int(request.GET.get("page_size", "{{ tabs[0].table.page_size|default(10) if tabs and tabs[0].get('table') else 10 }}"))
        except ValueError:
            page_size = 10
        if page_size not in (10, 20):
            page_size = 10

        # base queryset
        qs = {{ model }}Repo.qs().order_by("-id").values(
            "id"
            {% for n in fields|map(attribute='name') %}
                {% if n != "id" %}, "{{ n }}"{% endif %}
            {% endfor %}
        )

        paginator = Paginator(qs, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages or 1)

        rows = []
        for r in page_obj.object_list:
            row = {"id": r["id"]}
            {% if 'title' in fields|map(attribute='name')|list %}row["title"] = r.get("title") or f"{{ model }} #{r['id']}"{% endif %}
            {% if 'is_active' in fields|map(attribute='name')|list %}row["status"] = "Live" if r.get("is_active") else "Hidden"{% endif %}
            {% if 'updated_at' in fields|map(attribute='name')|list %}row["updated_at"] = r.get("updated_at").strftime("%Y-%m-%d %H:%M") if r.get("updated_at") else ""{% endif %}
            rows.append(row)

        table_ctx = {
            "table": {
                "id": "{{ view_name|lower }}Table",
                "headers": [
                    {% if 'title' in fields|map(attribute='name')|list %}"Title",{% endif %}
                    {% if 'is_active' in fields|map(attribute='name')|list %}"Status",{% endif %}
                    {% if 'updated_at' in fields|map(attribute='name')|list %}"Updated",{% endif %}
                    "Actions"
                ],
                "columns": [
                    {% if 'title' in fields|map(attribute='name')|list %}"title",{% endif %}
                    {% if 'is_active' in fields|map(attribute='name')|list %}"status",{% endif %}
                    {% if 'updated_at' in fields|map(attribute='name')|list %}"updated_at",{% endif %}
                    "actions"
                ],
                "rows": rows,
                "actions": [
                    {
                        "label": "Edit",
                        "class": "btn btn-sm btn-outline-primary",
                        "hx_get": "{{ app_label }}:{{ view_name|lower }}_edit_htmx",
                        "target": "#modal .modal-content",
                        "extra": 'data-bs-toggle="modal" data-bs-target="#modal"'
                    },
                    {
                        "label": "Delete",
                        "class": "btn btn-sm btn-outline-danger ms-2",
                        "hx_post": "{{ app_label }}:{{ view_name|lower }}_delete_htmx",
                        "hx_headers": "{\"HX-Trigger\":\"{{ view_name|lower }}Deleted\"}",
                        "hx_confirm": "Delete this item?"
                    }
                ],
                "hx": {
                    "triggers": "{{ view_name|lower }}Created, {{ view_name|lower }}Updated, {{ view_name|lower }}Deleted from:body",
                    "swap": "outerHTML"
                },
                "row_id_prefix": "row"
            },
            "pagination": {
                "page": page_obj.number,
                "page_size": page_size,
                "num_pages": paginator.num_pages,
                "count": paginator.count,
                "has_prev": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
                "prev": page_obj.previous_page_number() if page_obj.has_previous() else 1,
                "next": page_obj.next_page_number() if page_obj.has_next() else paginator.num_pages,
                # compact range (first, current-2..current+2, last)
                "range": [p for p in (
                    [1] +
                    [n for n in range(page_obj.number-2, page_obj.number+3) if 1 < n < paginator.num_pages] +
                    ([paginator.num_pages] if paginator.num_pages > 1 else [])
                ) if p == 1 or p == paginator.num_pages or abs(p - page_obj.number) <= 2]
            },
            "list_endpoint": "{% url app_label ~ ':' ~ view_name|lower ~ '_list_htmx' %}"
        }

        return render(request, self.template_name, table_ctx)


class {{ view_name }}CreateView(View):
    template_name = "{{ view_name|lower }}_form.html"
    def get(self, request):
        field_values = [{"name": f.name, "value": ""} for f in {{ model }}._meta.fields if f.name != "id"]
        return render(request, self.template_name, {"mode":"create","field_values":field_values})
    def post(self, request):
        data = {k: v for k, v in request.POST.dict().items() if k in {{ fields|map(attribute='name')|list|pyrepr }}}
        {{ model }}Repo.create(data)
        return trigger("{{ view_name|lower }}Created")

class {{ view_name }}UpdateView(View):
    template_name = "{{ view_name|lower }}_form.html"
    def get(self, request, pk:int):
        obj = get_object_or_404({{ model }}, pk=pk)
        fv = []
        for name in {{ fields|map(attribute='name')|list|pyrepr }}:
            if name != "id":
                fv.append({"name": name, "value": getattr(obj, name, "")})
        return render(request, self.template_name, {"mode":"edit","obj_id":pk,"field_values":fv})
    def post(self, request, pk:int):
        data = {k: v for k, v in request.POST.dict().items() if k in {{ fields|map(attribute='name')|list|pyrepr }}}
        {{ model }}Repo.update(pk, data)
        return trigger("{{ view_name|lower }}Updated")

class {{ view_name }}DeleteView(View):
    def post(self, request, pk:int):
        {{ model }}Repo.delete(pk)
        return trigger("{{ view_name|lower }}Deleted")
