import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import logging

# =====================================================
# 🔹 PATHS
# =====================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =====================================================
# 🔹 ENVIRONMENT
# =====================================================
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# =====================================================
# 🔹 BASIC SETTINGS
# =====================================================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "1").strip().lower() in ("1", "true", "yes")

ALLOWED_HOSTS = []

# =====================================================
# 🔹 APPLICATIONS
# =====================================================
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_ratelimit",
    "main.apps.MainConfig",
    "django_extensions",
]

# =====================================================
# 🔹 MIDDLEWARE
# =====================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "main.middleware.security_monitor.SecurityMonitorMiddleware",
    "loan_saathi_hub.middleware.ExceptionLoggingMiddleware",
]

ROOT_URLCONF = "loan_saathi_hub.urls"

# =====================================================
# 🔹 TEMPLATES
# =====================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.user_profile",
                "main.context_processors.ads_context",
            ],
        },
    },
]

WSGI_APPLICATION = "loan_saathi_hub.wsgi.application"

# =====================================================
# 🔹 DATABASE (Default fallback – overridden in local/render)
# =====================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# =====================================================
# 🔹 STATIC & MEDIA
# =====================================================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =====================================================
# 🔹 AUTH
# =====================================================
AUTH_USER_MODEL = "main.User"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# =====================================================
# 🔹 SAFE CACHE + SESSION + MESSAGE DEFAULTS
# =====================================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "loan-saathi-hub-cache",
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
RATELIMIT_USE_CACHE = "default"
RATELIMIT_CACHE = "default"

# =====================================================
# 🔹 DEFAULT AUTO FIELD
# =====================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================================
# 🔹 LOGGING
# =====================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
