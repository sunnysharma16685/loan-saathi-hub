from django.http import HttpResponseRedirect
from django.conf import settings

class ForceHTTPMiddleware:
    """
    🚦 Middleware: Redirects HTTPS → HTTP in local development.
    Prevents 'You're accessing the development server over HTTPS' warnings.
    Automatically logs a friendly message once per server start.
    """

    printed_warning = False  # static flag to avoid repeating logs

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ✅ Only active in DEBUG mode
        if settings.DEBUG:
            is_https = (
                request.is_secure() or 
                request.META.get("HTTP_X_FORWARDED_PROTO") == "https"
            )
            if is_https:
                http_url = request.build_absolute_uri().replace("https://", "http://", 1)
                
                # 🧠 Log only once per server start
                if not ForceHTTPMiddleware.printed_warning:
                    print(
                        "⚠️ [ForceHTTPMiddleware] Browser tried to use HTTPS on localhost — redirected to HTTP.\n"
                        "💡 Tip: Access your site at http://127.0.0.1:8000 instead of https://"
                    )
                    ForceHTTPMiddleware.printed_warning = True

                return HttpResponseRedirect(http_url)

        return self.get_response(request)
