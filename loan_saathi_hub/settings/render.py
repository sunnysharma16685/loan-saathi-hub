from .base import *
import os
import dj_database_url

# =====================================================
# 🌐 RENDER PRODUCTION SETTINGS
# =====================================================

DEBUG = False

# ✅ Allow only your live domains
ALLOWED_HOSTS = [
    "loansaathihub.in",
    "www.loansaathihub.in",
    "loansaathi-hub.onrender.com",
]

# =====================================================
# 🔹 DATABASE (PostgreSQL via Render DATABASE_URL)
# =====================================================
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# =====================================================
# 🔹 CACHING (Redis – Shared across all processes)
# =====================================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# =====================================================
# 🔹 EMAIL SETTINGS (Gmail SMTP for OTPs, Ads, etc.)
# =====================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "loansaathihub@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "Ridh@1637#sun113mayu")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =====================================================
# 🔹 CSRF / SECURITY / SSL
# =====================================================
CSRF_TRUSTED_ORIGINS = [
    "https://loansaathihub.in",
    "https://www.loansaathihub.in",
    "https://loansaathi-hub.onrender.com",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
REFERRER_POLICY = "strict-origin-when-cross-origin"

X_FRAME_OPTIONS = "DENY"

# =====================================================
# 🔹 STATIC FILES (Optimized for Render)
# =====================================================
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =====================================================
# 🔹 LOGGING (Minimal, Safe for Production)
# =====================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name} | {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# =====================================================
# 🔹 INFO
# =====================================================
print("✅ Loaded Render Production Settings (PostgreSQL + Redis + Gmail SMTP)")
