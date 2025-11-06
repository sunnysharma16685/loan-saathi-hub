import re
import logging
from django.http import HttpResponseForbidden

# Use Django’s security logger
logger = logging.getLogger("django.security")


class SecurityMonitorMiddleware:
    """
    🚨 Security Middleware for Loan Saathi Hub
    -------------------------------------------------
    • Detects and blocks obvious SQLi / XSS patterns.
    • Skips trusted routes (profile, dashboard, static files, payments).
    • Logs all suspicious requests safely in logs/security.log
    • Never breaks normal POST/JSON views (safe body handling).
    """

    BLOCK_PATTERNS = re.compile(
        r"(?i)("
        r"union\s+select|drop\s+table|insert\s+into|update\s+.*set\s+|"  # SQLi
        r"<script.*?>|onerror\s*=|onload\s*=|javascript:"               # XSS
        r")"
    )

    SAFE_PATH_PREFIXES = (
        "/login/",
        "/register/"
        "/profile/",
        "/dashboard",
        "/loan",
        "/static/",
        "/media/",
        "/payment/",
        "/support",
        "/feedback",
        "/complaint",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            path = request.path.lower()

            # ✅ Skip scanning for safe internal URLs
            if any(path.startswith(p) for p in self.SAFE_PATH_PREFIXES):
                return self.get_response(request)

            # Collect minimal request info
            query = str(request.GET).lower()
            form_data = str(request.POST).lower() if request.method == "POST" else ""
            payload = " ".join([path, query, form_data])

            # ✅ Read small JSON body safely (no double-read crash)
            if request.content_type and "application/json" in request.content_type:
                try:
                    if not hasattr(request, "_body_read"):
                        body_str = request.body.decode("utf-8", errors="ignore")
                        request._body_read = True
                        if len(body_str) < 5000:  # prevent heavy payload scanning
                            payload += " " + body_str.lower()
                except Exception as e:
                    logger.debug(f"Body read skipped: {e}")

            # ✅ Detect suspicious patterns
            if self.BLOCK_PATTERNS.search(payload):
                client_ip = (
                    request.META.get("HTTP_X_FORWARDED_FOR")
                    or request.META.get("REMOTE_ADDR")
                )
                logger.warning(
                    f"🚫 Blocked suspicious request from {client_ip}: {request.path}"
                )
                return HttpResponseForbidden(
                    "🚫 Suspicious activity detected and blocked by Security Monitor."
                )

        except Exception as e:
            # 🧩 Fail-safe: never block legitimate traffic on internal errors
            logger.error(f"SecurityMonitorMiddleware error: {e}")

        return self.get_response(request)
