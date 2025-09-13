from aiohttp import request
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import random
from django.views.decorators.http import require_http_methods

import time


def error_400(request, exception):
    context = {
        "title": "400 Bad Request",
    }
    return render(request, "errors/400.html", context=context, status=400)


def error_401(request, exception=None):
    context = {
        "title": "401 Unauthorized",
    }
    return render(request, "errors/401.html", context=context, status=401)


def error_403(request, exception):
    context = {
        "title": "403 Forbidden",
    }
    return render(request, "errors/403.html", context=context, status=403)


def error_404(request, exception=None):
    template = random.choice(["errors/404a.html", "errors/404b.html"])
    context = {"title": "404 Not Found"}
    return render(request, template, context=context, status=404)


def error_503(request, exception=None):
    context = {
        "title": "503 Service Unavailable",
    }
    return render(request, "errors/503.html", context=context, status=503)


def error_504(request, exception=None):
    context = {
        "title": "504 Gateway Timeout",
    }
    return render(request, "errors/504.html", context=context, status=504)


def error_500(request):
    context = {
        "title": "500 Internal Server Error",
    }
    return render(request, "errors/500.html", context=context, status=500)
