import re
import logging
from django.http import HttpResponseForbidden

logger = logging.getLogger("django.security")

class SecurityMonitorMiddleware:
    """
    🚨 Middleware to detect and block suspicious request patterns safely.
    Blocks obvious SQL injection or XSS attempts and logs them in logs/security.log.
    """

    BLOCK_PATTERNS = re.compile(
        r"(?i)("
        r"union\s+select|drop\s+table|insert\s+into|update\s+.*set\s+|"
        r"<script.*?>|onerror\s*=|onload\s*=|javascript:"
        r")"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # ✅ Avoid direct request.body read
            path = request.path
            query = str(request.GET)
            form_data = str(request.POST) if request.method == "POST" else ""
            payload = " ".join([path, query, form_data])

            # ✅ Only read .body if absolutely necessary (and only for JSON)
            if request.content_type and "application/json" in request.content_type:
                try:
                    body_str = request._body.decode("utf-8", errors="ignore") if hasattr(request, "_body") else ""
                except Exception:
                    body_str = ""
                payload += " " + body_str

            if self.BLOCK_PATTERNS.search(payload):
                client_ip = (
                    request.META.get("HTTP_X_FORWARDED_FOR")
                    or request.META.get("REMOTE_ADDR")
                )
                logger.warning(f"🚫 Blocked suspicious request from {client_ip}: {request.path}")
                return HttpResponseForbidden("🚫 Suspicious activity detected and blocked.")

        except Exception as e:
            # Don’t break user flow if middleware fails
            logger.error(f"SecurityMiddleware error: {e}")

        return self.get_response(request)
