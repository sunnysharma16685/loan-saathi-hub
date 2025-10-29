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
    """

    BLOCK_PATTERNS = re.compile(
        r"(?i)("
        r"union\s+select|drop\s+table|insert\s+into|update\s+.*set\s+|"  # SQLi
        r"<script.*?>|onerror\s*=|onload\s*=|javascript:"               # XSS
        r")"
    )

    # Paths that should NOT trigger blocking (normal user actions)
    SAFE_PATH_PREFIXES = (
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

            # ✅ Skip scanning safe internal URLs
            if any(path.startswith(p) for p in self.SAFE_PATH_PREFIXES):
                return self.get_response(request)

            # Collect minimal request data
            query = str(request.GET).lower()
            form_data = str(request.POST).lower() if request.method == "POST" else ""
            payload = " ".join([path, query, form_data])

            # ✅ Add JSON body if small and present
            if request.content_type and "application/json" in request.content_type:
                try:
                    body_str = request.body.decode("utf-8", errors="ignore")
                    if len(body_str) < 5000:  # prevent large body read
                        payload += " " + body_str.lower()
                except Exception:
                    pass

            # ✅ Check for malicious signatures
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
            # 🧩 Fail-safe: never block legitimate traffic if an error occurs
            logger.error(f"SecurityMonitorMiddleware error: {e}")

        return self.get_response(request)
