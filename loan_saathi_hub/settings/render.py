from .base import *
import os
import dj_database_url

# =====================================================
# 🌐 RENDER PRODUCTION SETTINGS
# =====================================================

DEBUG = False

# ✅ Allow live domains + Render subdomains
ALLOWED_HOSTS = [
    "loansaathihub.in",
    "www.loansaathihub.in",
    "loan-saathi-hub.onrender.com",
    # ✅ Automatically trust all Render environments (staging, preview, etc.)
    ".onrender.com",
    # ✅ Local dev fallback
    "127.0.0.1",
    "localhost",
]

# ✅ Auto-detect Render host dynamically (works for staging, preview, etc.)
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME") or os.getenv("RENDER_EXTERNAL_URL")

# 🧩 Normalize host (remove scheme if present)
if render_host:
    render_host = render_host.replace("https://", "").replace("http://", "").strip("/")
    if render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_host)

print(f"✅ Detected Render Host: {render_host}")
print(f"✅ ALLOWED_HOSTS: {ALLOWED_HOSTS}")


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
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"  # ✅ must be string
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "loansaathihub@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "vbik uaho dnfa jmtk")  # 🧠 load from Render env
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =====================================================
# 🔹 CSRF / SECURITY / SSL
# =====================================================
CSRF_TRUSTED_ORIGINS = [
    "https://loansaathihub.in",
    "https://www.loansaathihub.in",
    "https://loan-saathi-hub.onrender.com",
]

# ✅ Auto-trust staging/previews too
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
# 🔹 INFO
# =====================================================
env_label = "STAGING" if render_host and "staging" in render_host else "PRODUCTION"
print(f"✅ Loaded Render {env_label} Settings (PostgreSQL + Redis + Gmail SMTP)")
print(f"✅ Detected Render Host: {render_host}")
print(f"✅ ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"✅ CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
