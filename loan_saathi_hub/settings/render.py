"""
Render Production Settings
Safe, Redis-Free, Neon-Ready
"""

from .base import *
import os
import sys
import builtins
import logging
import dj_database_url


# =====================================================
# 🚫 1) HARD DISABLE REDIS (for Render)
# =====================================================
sys.modules["django_redis"] = None
sys.modules["redis"] = None

_original_import = builtins.__import__

def no_redis_import(name, *args, **kwargs):
    if name.startswith(("redis", "django_redis")):
        raise ImportError("🚫 Redis disabled on Render")
    return _original_import(name, *args, **kwargs)

builtins.__import__ = no_redis_import

logging.warning("🚫 Redis forcibly disabled on Render environment")


# =====================================================
# 🌐 2) PRODUCTION MODE
# =====================================================
DEBUG = False

ALLOWED_HOSTS = [
    "loansaathihub.in",
    "www.loansaathihub.in",
    "loan-saathi-hub.onrender.com",
    ".onrender.com",
    "127.0.0.1",
    "localhost",
]

# Auto-add dynamic Render hostname
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME") or os.getenv("RENDER_EXTERNAL_URL")
if render_host:
    render_host = render_host.replace("https://", "").replace("http://", "").strip("/")
    if render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_host)

print("✅ Detected Render Host:", render_host)
print("✅ ALLOWED_HOSTS:", ALLOWED_HOSTS)


# =====================================================
# 🟦 3) DATABASE → NEON POSTGRESQL
# =====================================================
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}


# =====================================================
# ⚠️ 4) CACHE → LocMem ONLY (100% No Redis)
# =====================================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "render-locmem",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
RATELIMIT_USE_CACHE = "default"
RATELIMIT_CACHE = "default"

SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003", "django_ratelimit.W001"]


# =====================================================
# 📧 5) EMAIL SETTINGS
# =====================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# =====================================================
# 🔐 6) SECURITY / CSRF / SSL
# =====================================================
CSRF_TRUSTED_ORIGINS = [
    "https://loansaathihub.in",
    "https://www.loansaathihub.in",
    "https://loan-saathi-hub.onrender.com",
]

if render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

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
# 📁 7) STATIC FILES (Whitenoise)
# =====================================================
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# =====================================================
# 📝 8) LOGGING
# =====================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name} | {message}", "style": "{"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}


# =====================================================
# 🌍 9) TIMEZONE
# =====================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


print("✅ Loaded PRODUCTION Render Settings (Neon + No Redis + Secure)")
print("✅ CSRF_TRUSTED_ORIGINS:", CSRF_TRUSTED_ORIGINS)
