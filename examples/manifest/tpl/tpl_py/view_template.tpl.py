{# ---------- shared imports ---------- #}
import importlib
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import TemplateView

{# convenience #}
{% set single = (tabs|length == 1) %}
{% set default_tab = tabs[0].slug if tabs else 'default' %}
{% set required_ranks_map -%}
{
{% for tab in tabs %}    {{ tab.slug|pyrepr }}: {{ tab.required_rank }}{% if not loop.last %},{% endif %}
{% endfor %}
}
{%- endset %}

{# ---------- SINGLE ROUTE: Function-based view ---------- #}
{% if single %}
# Single-route: simple function-based view for speed & simplicity
def {{ view_name|lower }}(request):
    tab = {{ default_tab|pyrepr }}
    required_ranks = {{ required_ranks_map }}
    # rank check (authenticated + rank threshold)
    try:
        rank = getattr(request.user, "rank", 0)
    except Exception:
        rank = 0
    if not (request.user.is_authenticated and rank >= required_ranks.get(tab, 1000)):
        return HttpResponseForbidden("Access Denied")

    # HTMX partial behavior (optional header "X-Partial": true)
    {% set tab_tpl = tabs[0].form_template %}
    if getattr(request, "htmx", False) and request.headers.get("X-Partial"):
        return render(request, "{{ tab_tpl }}", {"tab": tab, "user": request.user})

    # Optional form handling for POST
    if request.method == "POST":
        mod_name = f"core.forms.{{ view_name|lower }}_{tab}_form"
        try:
            mod = importlib.import_module(mod_name)
            cls_name = f"{tab.title().replace('_','')}Form"
            form_cls = getattr(mod, cls_name)
        except Exception:
            form_cls = None

        if form_cls is None:
            return HttpResponse("Form not available for this route", status=400)

        form = form_cls(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save() if hasattr(form, "save") else None
            resp = render(request, "{{ tab_tpl }}", {"tab": tab, "user": request.user, "saved": True, "obj": obj})
            resp["HX-Trigger"] = '{"toast": {"message": "Saved!", "type": "success"}}'
            return resp
        return render(request, "{{ tab_tpl }}", {"tab": tab, "user": request.user, "form": form})

    # GET: full-page render
    return render(request, "{{ default_template }}", {
        "tab": tab,
        "tab_template": "{{ tab_tpl }}",
        "title": "{{ title }}",
        "subtitle": "{{ subtitle }}",
        "user": request.user,
    })

{% else %}
{# ---------- MULTI ROUTE: Class-based TemplateView multiplexer ---------- #}
class {{ view_name }}(TemplateView):
    template_name = "{{ default_template }}"
    {% if lti_template %}lti_template_name = "{{ lti_template }}"{% endif %}
    http_method_names = ["get", "post"]
    ALLOWED_TABS = {{ allowed_tabs }}
    PARTIALS = {
    {% for tab in tabs %}    {{ tab.slug|pyrepr }}: {{ tab.form_template|pyrepr }}{% if not loop.last %},{% endif %}
    {% endfor %}
    }
    {% if partials_lti %}
    PARTIALS_LTI = {{ partials_lti }}
    {% else %}
    PARTIALS_LTI = PARTIALS
    {% endif %}

    def _tab(self):
        tab = (self.request.headers.get("X-Tab") or {{ default_tab|pyrepr }}).lower()
        return tab if tab in self.ALLOWED_TABS else {{ default_tab|pyrepr }}

    def has_tab_access(self, user, tab):
        required_ranks = {{ required_ranks_map }}
        try:
            rank = getattr(user, "rank", 0)
        except Exception:
            rank = 0
        return user.is_authenticated and rank >= required_ranks.get(tab, 1000)

    def _partials(self):
        # If you have LTI detection, swap templates; otherwise use PARTIALS
        is_lti = getattr(self, "is_lti", lambda: False)
        return self.PARTIALS_LTI if is_lti() else self.PARTIALS

    def _form_class(self, tab):
        mod_name = f"core.forms.{{ view_name|lower }}_{tab}_form"
        try:
            mod = importlib.import_module(mod_name)
            cls_name = f"{tab.title().replace('_','')}Form"
            return getattr(mod, cls_name)
        except Exception:
            return None

    def get(self, request, *args, **kwargs):
        tab = self._tab()
        if not self.has_tab_access(request.user, tab):
            return HttpResponseForbidden("Access Denied")

        partials = self._partials()
        if getattr(request, "htmx", False) and request.headers.get("X-Partial"):
            return render(request, partials[tab], {"tab": tab, "user": request.user})
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        tab = self._tab()
        if not self.has_tab_access(request.user, tab):
            return HttpResponseForbidden("Access Denied")

        partials = self._partials()
        form_cls = self._form_class(tab)
        if form_cls is None:
            return HttpResponse("Form not available for tab", status=400)

        form = form_cls(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save() if hasattr(form, "save") else None
            resp = render(request, partials[tab], {"tab": tab, "user": request.user, "saved": True, "obj": obj})
            resp["HX-Trigger"] = '{"toast": {"message": "Saved!", "type": "success"}}'
            return resp
        return render(request, partials[tab], {"tab": tab, "user": request.user, "form": form})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tab = self._tab()
        partials = self._partials()
        ctx.update({
            "tab": tab,
            "tab_template": partials[tab],
            "title": "{{ title }}",
            "subtitle": "{{ subtitle }}",
        })
        return ctx
{% endif %}
