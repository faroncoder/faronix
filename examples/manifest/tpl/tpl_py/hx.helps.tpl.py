# hx_helpers.tpl.py — AUTO-GENERATED: small HX utilities
from django.http import HttpResponse


def trigger(event: str, body: str = "") -> HttpResponse:
    resp = HttpResponse(body)
    resp["HX-Trigger"] = event
    return resp
