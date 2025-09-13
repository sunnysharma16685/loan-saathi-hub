import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------
# ENVIRONMENT DETECTION
# ---------------------------
# Local dev में .env.local load होगा
local_env_file = BASE_DIR / ".env.local"
if local_env_file.exists():
    load_dotenv(local_env_file)

# ---------------------------
# SECURITY
# ---------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")

DEBUG = os.getenv("DJANGO_DEBUG", "0").strip().lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

# Render / proxy HTTPS fix
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Debugging line (optional, remove in prod)
print("🌍 ALLOWED_HOSTS loaded:", ALLOWED_HOSTS)

# ---------------------------
# APPLICATIONS
# ---------------------------
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "loan_saathi_hub.urls"

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
                "main.context_processors.testing_mode",
            ],
        },
    },
]

WSGI_APPLICATION = "loan_saathi_hub.wsgi.application"

# ---------------------------
# DATABASE
# ---------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render (production) → DATABASE_URL से
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
elif os.getenv("DB_NAME"):
    # Local Postgres (DB_* vars से)
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    # Fallback SQLite (development emergency)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------
# CUSTOM USER MODEL
# ---------------------------
AUTH_USER_MODEL = "main.User"

# ---------------------------
# STATIC & MEDIA
# ---------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
    if not DEBUG
    else "django.contrib.staticfiles.storage.StaticFilesStorage"
)

# ---------------------------
# EMAIL
# ---------------------------
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").strip().lower() in ("1", "true", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# ---------------------------
# SECURITY HEADERS
# ---------------------------
SECURE_SSL_REDIRECT = (
    os.getenv("SECURE_SSL_REDIRECT", "True").strip().lower() in ("1", "true", "yes")
    if not DEBUG else False
)
SESSION_COOKIE_SECURE = (
    os.getenv("SESSION_COOKIE_SECURE", "True").strip().lower() in ("1", "true", "yes")
    if not DEBUG else False
)
CSRF_COOKIE_SECURE = (
    os.getenv("CSRF_COOKIE_SECURE", "True").strip().lower() in ("1", "true", "yes")
    if not DEBUG else False
)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000")) if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True").strip().lower() in ("1", "true", "yes")
    if not DEBUG else False
)
SECURE_HSTS_PRELOAD = (
    os.getenv("SECURE_HSTS_PRELOAD", "True").strip().lower() in ("1", "true", "yes")
    if not DEBUG else False
)

X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY")

# ---------------------------
# CSRF TRUSTED ORIGINS
# ---------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://www.loansaathihub.in",
    "https://loansaathihub.in",
    "https://loansaathi-hub.onrender.com",
]

# ---------------------------
# DEFAULT PRIMARY KEY
# ---------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
