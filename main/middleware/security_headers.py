from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add browser-level security headers like CSP, Referrer, and Permissions."""
    def process_response(self, request, response):
        response["X-Frame-Options"] = "DENY"
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' data: https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com"
        )
        return response
