import threading
import json
import logging
import time
from django.conf import settings
from django.shortcuts import redirect
from urllib.parse import urlencode, urlsplit
from django.urls import reverse, NoReverseMatch
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from django.db import connection

_thread_locals = threading.local()


def set_debug_info(info):
    _thread_locals.debug_info = info


def get_debug_info():
    return getattr(_thread_locals, "debug_info", None)


REDACT = {"password", "new_password", "confirm_password", "csrfmiddlewaretoken"}


class DebugInfoMiddleware:
    """
    Middleware to collect debug info and make it available for templates.
    Only active if settings.DEBUG is True.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            # Example: collect request info, user, etc.
            debug_info = {
                "path": request.path,
                "method": request.method,
                "user": str(getattr(request, "user", None)),
                "GET": dict(request.GET),
                "POST": dict(request.POST),
                # Add more as needed
            }
            set_debug_info(debug_info)
        response = self.get_response(request)
        return response


class HTMXLoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.append_next = False  # Always disable appending next

    def _login_path(self) -> str:
        """Resolve LOGIN_URL to a path string (no scheme/host)."""
        lu = settings.LOGIN_URL
        if ":" in lu:  # namespaced route
            try:
                return reverse(lu)
            except NoReverseMatch:
                # fall back to raw value if someone misconfigured LOGIN_URL
                return lu
        return lu  # already a path like "/login/"

    def __call__(self, request):
        resp = self.get_response(request)

        # only adjust redirects
        if resp.status_code not in (301, 302):
            return resp

        location = resp.headers.get("Location", "")
        if not location:
            return resp

        login_path = self._login_path()
        # Compare by path (Location might be absolute)
        loc_path = urlsplit(location).path

        # Is this redirect going to the login page?
        if not loc_path.startswith(login_path):
            return resp

        # Respect an HX-Redirect already set by a view
        if resp.headers.get("HX-Redirect"):
            return resp

        # Do not append ?next= to login redirect URLs

        # For HTMX requests, convert 302 → HX-Redirect (no fragment injection)
        if request.headers.get("HX-Request") == "true":
            resp.status_code = 200
            resp["HX-Redirect"] = location

        return resp


logger = logging.getLogger("htmx")


def _redact(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        out[k] = "***" if k in REDACT else v
    return out


class HtmxDebugSleepMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG and request.headers.get("HX-Request") == "true":
            ms = request.headers.get("X-Debug-Sleep") or request.GET.get("_sleep")
            try:
                delay = int(ms or 0)
            except ValueError:
                delay = 0
            if delay > 0:
                time.sleep(delay / 1000.0)
        return self.get_response(request)


logger = logging.getLogger("htmx")
REDACT = {"password", "new_password", "confirm_password", "csrfmiddlewaretoken"}


def _redact(d: dict) -> dict:
    return {k: ("***" if k in REDACT else v) for k, v in d.items()}


class HTMXRequestLogger(MiddlewareMixin):
    def process_request(self, request):
        # only track when we actually intend to log (prod or env toggle)
        if (
            getattr(settings, "HTMX_SERVER_LOG", False)
            and request.headers.get("HX-Request") == "true"
        ):
            request.__t0 = time.perf_counter()
            request.__req_id = (
                request.headers.get("X-Request-ID") or f"hx-{get_random_string(8)}"
            )

    def process_response(self, request, response):
        try:
            if getattr(settings, "HTMX_SERVER_LOG", False) and hasattr(
                request, "__req_id"
            ):
                # In prod, keep server-only by default:
                if getattr(settings, "HTMX_ECHO_REQUEST_ID", False):
                    response.headers["X-Request-ID"] = request.__req_id

                dt_ms = (
                    round((time.perf_counter() - request.__t0) * 1000.0, 1)
                    if hasattr(request, "__t0")
                    else None
                )

                post_data = {}
                if request.method in ("POST", "PUT", "PATCH"):
                    try:
                        post_data = _redact(dict(request.POST.items()))
                    except Exception:
                        post_data = {"_warn": "unreadable_post"}

                payload = {
                    "id": request.__req_id,
                    "method": request.method,
                    "path": request.path,
                    "status": getattr(response, "status_code", None),
                    "ms": dt_ms,
                    "user": getattr(getattr(request, "user", None), "username", None),
                    "hx": request.headers.get("HX-Request"),
                    "x_tab": request.headers.get("X-Tab"),
                    "x_partial": request.headers.get("X-Partial"),
                    "ua": request.META.get("HTTP_USER_AGENT"),
                    "post": post_data,
                    "ts": now().isoformat(),
                    "db_queries": q_count,
                    "referer": request.META.get("HTTP_REFERER"),
                }
                logger.info(json.dumps(payload, ensure_ascii=False))
        finally:
            return response
