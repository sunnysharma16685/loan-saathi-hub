from .base import *
import os
import dj_database_url

DEBUG = True  # keep true for safe testing

ALLOWED_HOSTS = [
    "loan-saathi-hub-staging.onrender.com",
]

DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=False,
    )
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CSRF_TRUSTED_ORIGINS = [
    "https://loan-saathi-hub-staging.onrender.com",
]

print("🧠 Loaded STAGING settings (Postgres + Gmail SMTP)")
