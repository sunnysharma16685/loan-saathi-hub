import re
import logging
from django.http import HttpResponseForbidden

logger = logging.getLogger("django.security")


class SecurityMonitorMiddleware:
    """
    🚨 Middleware to detect and block suspicious request patterns.
    Blocks obvious SQL injection or XSS attempts and logs them in logs/security.log.
    """

    # ✅ Case-insensitive regex moved correctly to start of pattern
    BLOCK_PATTERNS = re.compile(
        r"(?i)("  # case-insensitive flag must come first
        r"union\s+select|drop\s+table|insert\s+into|update\s+.*set\s+|"  # SQLi patterns
        r"<script.*?>|onerror\s*=|onload\s*=|javascript:"               # XSS patterns
        r")"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        payload = " ".join([
            request.path,
            str(request.GET),
            str(request.POST),
            str(request.body),
        ])

        if self.BLOCK_PATTERNS.search(payload):
            client_ip = (
                request.META.get("HTTP_X_FORWARDED_FOR")
                or request.META.get("REMOTE_ADDR")
            )
            logger.warning(f"🚫 Blocked suspicious request from {client_ip}: {request.path}")
            return HttpResponseForbidden("🚫 Suspicious activity detected and blocked.")

        return self.get_response(request)
