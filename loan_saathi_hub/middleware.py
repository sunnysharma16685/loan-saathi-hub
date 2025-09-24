import logging
import traceback

logger = logging.getLogger(__name__)

class ExceptionLoggingMiddleware:
    """
    Middleware to log every unhandled exception with full traceback.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error(
                "🔥 Exception on %s: %s\n%s",
                request.path,
                str(e),
                traceback.format_exc(),
            )
            raise
