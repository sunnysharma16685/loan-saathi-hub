from .base import *
import os
import sys
import builtins
import logging
import dj_database_url

# =====================================================
# 🚫 HARD DISABLE REDIS IMPORTS (before anything else)
# =====================================================
print("🔥 Using render.py — Redis forcibly blocked at import level")

# Completely block any attempt to import or use django_redis
sys.modules["django_redis"] = None
builtins.__import_original__ = builtins.__import__


def safe_import(name, *args, **kwargs):
    if name.startswith("django_redis"):
        raise ImportError("🚫 django_redis forcibly disabled on Render")
    return builtins.__import_original__(name, *args, **kwargs)


builtins.__import__ = safe_import

# =====================================================
# 🌐 RENDER PRODUCTION SETTINGS
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

# Auto-detect Render host dynamically
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME") or os.getenv("RENDER_EXTERNAL_URL")
if render_host:
    render_host = render_host.replace("https://", "").replace("http://", "").strip("/")
    if render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_host)

print(f"✅ Detected Render Host: {render_host}")
print(f"✅ ALLOWED_HOSTS: {ALLOWED_HOSTS}")

# =====================================================
# 🔹 DATABASE (PostgreSQL via Render)
# =====================================================
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# =====================================================
# 🔹 CACHING — Redis Disabled, Use LocMemCache
# =====================================================
logging.warning("⚠️ Running on Render — Redis is fully disabled, using LocMemCache only.")
os.environ["DJANGO_REDIS_IGNORE_EXCEPTIONS"] = "True"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "loan-saathi-render-cache",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
RATELIMIT_USE_CACHE = "default"
RATELIMIT_CACHE = "default"

# =====================================================
# 🔹 EMAIL SETTINGS (Gmail SMTP)
# =====================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "loansaathihub@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "vbik uaho dnfa jmtk")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =====================================================
# 🔹 SECURITY & CSRF / SSL
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
# 🔹 STATIC FILES (Whitenoise)
# =====================================================
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =====================================================
# 🔹 LOGGING
# =====================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

# =====================================================
# 🔹 ENVIRONMENT INFO
# =====================================================
env_label = "PRODUCTION"
print(f"✅ Loaded Render {env_label} Settings (PostgreSQL + LocMemCache + Gmail SMTP)")
print(f"✅ CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
