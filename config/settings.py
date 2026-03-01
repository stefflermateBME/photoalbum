from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Secret és debug mód
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-unsafe-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"

# Engedélyezett hosztok és CSRF‑eredetek
allowed = os.getenv("DJANGO_ALLOWED_HOSTS", ".openshiftapps.com,localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in allowed.split(",") if h.strip()]
csrf = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [x.strip() for x in csrf.split(",") if x.strip()] if csrf.strip() else []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "album",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Adatbázis: DATABASE_URL alapján (postgres)
DATABASES = {
    "default": dj_database_url.config(default=os.environ.get("DATABASE_URL"))
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "hu"
TIME_ZONE = "Europe/Budapest"
USE_I18N = True
USE_TZ = True

# Statikus fájlok
STATIC_URL = "/static/"
# STATIC_ROOT environmentből vagy fallbackként /app/staticfiles (OpenShift)
STATIC_ROOT = os.getenv("DJANGO_STATIC_ROOT", os.getenv("STATIC_ROOT", "/app/staticfiles"))
# WhiteNoise tároló használata
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Feltöltött médiafájlok
MEDIA_URL = "/media/"
# MEDIA_ROOT environmentből vagy fallbackként /data/media
MEDIA_ROOT = os.getenv("DJANGO_MEDIA_ROOT", os.getenv("MEDIA_ROOT", "/data/media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "photo-list"
LOGOUT_REDIRECT_URL = "photo-list"

# Proxy / OpenShift Route HTTPS kezelése
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Biztonsági beállítások productionben
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False  # a TLS termináció az OpenShift Route-on történik