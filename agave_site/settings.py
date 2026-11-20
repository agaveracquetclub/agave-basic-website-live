import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-development-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [x.strip() for x in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if x.strip()]
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store.apps.StoreConfig",
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

ROOT_URLCONF = "agave_site.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "store.context_processors.cart_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "agave_site.wsgi.application"
ASGI_APPLICATION = "agave_site.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=60,
        ssl_require=os.getenv("DB_SSL_REQUIRE", "False").lower() == "true",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_MANIFEST_STRICT = False
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
if os.getenv("SUPABASE_S3_ENDPOINT"):
    storage_options = {
        "endpoint_url": os.environ["SUPABASE_S3_ENDPOINT"],
        "access_key": os.environ["SUPABASE_S3_ACCESS_KEY"],
        "secret_key": os.environ["SUPABASE_S3_SECRET_KEY"],
        "bucket_name": os.getenv("SUPABASE_S3_BUCKET", "agave-products"),
        "region_name": os.getenv("SUPABASE_S3_REGION", "us-east-1"),
        "default_acl": None,
        "querystring_auth": not bool(os.getenv("SUPABASE_STORAGE_PUBLIC_DOMAIN")),
        "file_overwrite": False,
    }
    if os.getenv("SUPABASE_STORAGE_PUBLIC_DOMAIN"):
        storage_options["custom_domain"] = os.environ["SUPABASE_STORAGE_PUBLIC_DOMAIN"]
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": storage_options}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "store:catalog"
LOGOUT_REDIRECT_URL = "store:home"
LOGIN_URL = "login"

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Agave Racquet Club <no-reply@example.com>")

MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY", "")
MERCADOPAGO_WEBHOOK_SECRET = os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "")
MERCADOPAGO_SUCCESS_URL = os.getenv("MERCADOPAGO_SUCCESS_URL", "")
MERCADOPAGO_FAILURE_URL = os.getenv("MERCADOPAGO_FAILURE_URL", "")
MERCADOPAGO_PENDING_URL = os.getenv("MERCADOPAGO_PENDING_URL", "")
ENVIA_API_TOKEN = os.getenv("ENVIA_API_TOKEN", "")
ENVIA_RATE_URL = os.getenv("ENVIA_RATE_URL", "https://api-test.envia.com/ship/rate/")
ENVIA_SHIPMENT_URL = os.getenv("ENVIA_SHIPMENT_URL", "https://api-test.envia.com/ship/generate/")
STOCK_HOLD_MINUTES = int(os.getenv("STOCK_HOLD_MINUTES", "15"))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

