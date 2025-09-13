# core/mixins.py
from django.views.generic.base import TemplateResponseMixin
from django.shortcuts import render


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
