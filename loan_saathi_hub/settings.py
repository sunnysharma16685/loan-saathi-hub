import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import logging
import traceback


# =====================================================
# 🔹 ENVIRONMENT DETECTION (Final, Safe & Cross-Platform)
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)

# ✅ Priority order: Render → Local → Default
env_files = [
    BASE_DIR / ".env.render",
    BASE_DIR / ".env.local",
    BASE_DIR / ".env",
]

loaded_env = None
for env_path in env_files:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        loaded_env = env_path.name
        break

if loaded_env:
    print(f"✅ Loaded environment file: {loaded_env}")
    logger.info(f"Loaded environment file: {loaded_env}")
else:
    print("⚠️ No .env file found — using system environment variables.")
    logger.warning("No .env file found — using system environment variables.")

# ✅ Parse DEBUG safely (treats '1', 'true', 'yes' as True)
DEBUG = os.getenv("DJANGO_DEBUG", "0").strip().lower() in ("1", "true", "yes")
print(f"🔍 DEBUG = {DEBUG} | DJANGO_DEBUG = {os.getenv('DJANGO_DEBUG')}")
logger.info(f"DEBUG = {DEBUG} | DJANGO_DEBUG = {os.getenv('DJANGO_DEBUG')}")

# =====================================================
# 🔹 SECURITY BASICS
# =====================================================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "0").strip().lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,loansaathihub.in,www.loansaathihub.in"
    ).split(",")
    if h.strip()
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
    
    # Local app
    "main.apps.MainConfig",
]

# =====================================================
# 🔹 MIDDLEWARE
# =====================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "main.middleware.security_headers.SecurityHeadersMiddleware",  # ✅ add this custom one
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "main.middleware.profile_check.ProfileCompletionMiddleware",
    "main.middleware.security_monitor.SecurityMonitorMiddleware",


    # 🔥 Exception logging middleware (last)
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

                # Custom context processors
                "main.context_processors.user_profile",
                "main.context_processors.testing_mode",
                "main.context_processors.ads_context",
            ],
        },
    },
]

WSGI_APPLICATION = "loan_saathi_hub.wsgi.application"

# =====================================================
# 🔹 DATABASE
# =====================================================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
elif os.getenv("DB_NAME"):
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
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =====================================================
# 🔹 AUTHENTICATION
# =====================================================
AUTH_USER_MODEL = "main.User"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

# =====================================================
# 🔹 PASSWORD VALIDATORS
# =====================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =====================================================
# 🔹 LANGUAGE & TIMEZONE
# =====================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# =====================================================
# 🔹 STATIC & MEDIA
# =====================================================
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

# =====================================================
# 🔹 EMAIL SETTINGS
# =====================================================
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

# =====================================================
# 🔹 SECURITY HEADERS
# =====================================================
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    REFERRER_POLICY = "strict-origin-when-cross-origin"
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

X_FRAME_OPTIONS = "DENY"

# =====================================================
# 🔹 CSRF TRUSTED ORIGINS
# =====================================================
CSRF_TRUSTED_ORIGINS = [
    "https://www.loansaathihub.in",
    "https://loansaathihub.in",
    "https://loansaathi-hub.onrender.com",
]
if DEBUG:
    CSRF_TRUSTED_ORIGINS += ["http://127.0.0.1:8000", "http://localhost:8000"]

# =====================================================
# 🔹 DEFAULTS
# =====================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================================
# 🔹 LOGGING (Enhanced)
# =====================================================
LOG_DIR = BASE_DIR / "logs"
try:
    LOG_DIR.mkdir(exist_ok=True)
except Exception:
    pass

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
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": str(LOG_DIR / "app_events.log"),
            "formatter": "verbose",
        },
        "errors": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": str(LOG_DIR / "errors.log"),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file", "errors"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
}

# =====================================================
# 🔹 RAZORPAY SETTINGS
# =====================================================
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    if DEBUG:
        logging.getLogger(__name__).info("✅ Razorpay keys loaded (development).")
else:
    logging.getLogger(__name__).warning("⚠️ Razorpay keys missing; check .env or Render settings.")

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"
RAZORPAY_ORDER_URL = f"{RAZORPAY_API_BASE}/orders"
RAZORPAY_PAYMENT_URL = f"{RAZORPAY_API_BASE}/payments"

# -----------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "loan-saathi-hub-cache",
    }
}


# Add to settings.py (bottom)------------------------------------
SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003", "django_ratelimit.W001"]

	