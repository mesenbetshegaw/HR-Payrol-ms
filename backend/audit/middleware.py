"""Middleware that attaches request context to the current thread for audit logging."""
from __future__ import annotations

import threading

_local = threading.local()


def get_current_request():
    return getattr(_local, "request", None)


def get_current_actor():
    request = get_current_request()
    if request and hasattr(request, "user") and request.user.is_authenticated:
        return request.user
    return None


def get_client_ip(request) -> str | None:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditMiddleware:
    """Store the current request on thread-local so audit service can access it."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.request = request
        response = self.get_response(request)
        _local.request = None
        return response
