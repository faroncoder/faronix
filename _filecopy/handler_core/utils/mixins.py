# core/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateResponseMixin
from django.shortcuts import render


class HTMXLoginRequiredMixin(LoginRequiredMixin):
    """
    If the request is HTMX, render the login partial in-place with 401,
    so the URL bar never changes. Otherwise, fall back to normal redirect.
    """

    def handle_no_permission(self):
        # Works if you use django-htmx (request.htmx). You can also check header:
        # if self.request.headers.get("HX-Request") == "true":
        if getattr(self.request, "htmx", False):
            return render(self.request, "auth/login.html", status=401)
        return super().handle_no_permission()


class LTIModeMixin(TemplateResponseMixin):
    """
    Adds is_lti & lti_roles to context and lets the view pick an LTI-specific shell.
    """

    lti_template_name: str | None = None

    def is_lti(self) -> bool:
        # set in your /lti/launch
        return bool(getattr(self.request, "session", {}).get("is_lti"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_lti"] = self.is_lti()
        ctx["lti_roles"] = self.request.session.get("lti_roles")  # optional
        return ctx

    def get_template_names(self):
        if self.is_lti() and self.lti_template_name:
            return [self.lti_template_name]
        return super().get_template_names()
