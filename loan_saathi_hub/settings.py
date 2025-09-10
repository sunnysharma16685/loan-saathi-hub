import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------
# BASE DIR & ENV
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------
# HELPERS
# ---------------------------
def _bool(env_value, default=False):
    if env_value is None:
        return default
    return str(env_value).strip().lower() in ("1", "true", "yes", "on")

def _list(env_value, default=None, sep=","):
    raw = env_value if env_value is not None else ("" if default is None else default)
    return [p.strip() for p in str(raw).split(sep) if p.strip()]

# ---------------------------
# SECURITY
# ---------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")

# Use environment variable DEBUG for production. Defaults False (safe for Render)
DEBUG = _bool(os.getenv("DEBUG", "False"), default=False)

# If behind a proxy/load balancer (e.g., Render)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ALLOWED_HOSTS
# Example .env → ALLOWED_HOSTS=127.0.0.1,localhost,loansaathi-hub.onrender.com,www.loansaathihub.in
ALLOWED_HOSTS = _list(
    os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost,0.0.0.0,loansaathi-hub.onrender.com,www.loansaathihub.in"
    )
)

# ---------------------------
# APPLICATIONS
# ---------------------------
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",  # helper for dev if whitenoise installed
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",   # your app
]

# ---------------------------
# MIDDLEWARE
# ---------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must be after SecurityMiddleware
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
# DATABASE (robust)
# ---------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        import dj_database_url
        db_config = dj_database_url.parse(DATABASE_URL, conn_max_age=600)

        # Always enforce sslmode=require for Supabase/remote DB
        db_config.setdefault("OPTIONS", {})
        db_config["OPTIONS"]["sslmode"] = "require"

        DATABASES = {"default": db_config}
    except Exception:
        # fallback manual config (rarely needed)
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("DB_NAME", "postgres"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": os.getenv("DB_PASSWORD", ""),
                "HOST": os.getenv("DB_HOST", "localhost"),
                "PORT": os.getenv("DB_PORT", "5432"),
                "OPTIONS": {"sslmode": "require"},
            }
        }
else:
    # local fallback (no DATABASE_URL provided)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "postgres"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

# ---------------------------
# CUSTOM USER MODEL
# ---------------------------
AUTH_USER_MODEL = "main.User"

# ---------------------------
# PASSWORDS
# ---------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------
# LANGUAGE / TIMEZONE
# ---------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------
# STATIC & MEDIA
# ---------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
else:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------
# EMAIL CONFIG
# ---------------------------
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USE_TLS = _bool(os.getenv("EMAIL_USE_TLS", True))
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# ---------------------------
# SUPABASE CONFIG
# ---------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# ---------------------------
# SECURITY & COOKIES
# ---------------------------
if DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
else:
    SECURE_SSL_REDIRECT = _bool(os.getenv("SECURE_SSL_REDIRECT", "True"))
    SESSION_COOKIE_SECURE = _bool(os.getenv("SESSION_COOKIE_SECURE", "True"))
    CSRF_COOKIE_SECURE = _bool(os.getenv("CSRF_COOKIE_SECURE", "True"))
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _bool(os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True"))
    SECURE_HSTS_PRELOAD = _bool(os.getenv("SECURE_HSTS_PRELOAD", "True"))

X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY")

if ALLOWED_HOSTS:
    csf_trusted = []
    for host in ALLOWED_HOSTS:
        host = host.strip()
        if not host:
            continue
        # Hostname cleanup
        if not host.startswith("http"):
            csf_trusted.append(f"https://{host}")
        else:
            csf_trusted.append(host)
    CSRF_TRUSTED_ORIGINS = csf_trusted

# ---------------------------
# DEFAULT PRIMARY KEY
# ---------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------
# LOGGING
# ---------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO" if not DEBUG else "DEBUG"},
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO" if not DEBUG else "DEBUG",
            "propagate": False,
        }
    },
}
