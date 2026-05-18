"""Settings base compartilhados entre dev e prod.

Decisoes:
- pt-br + America/Sao_Paulo (memoria projeto convencoes)
- Argon2 como primeiro password hasher (resistente a GPU/ASIC)
- Conexao app_user (NOBYPASSRLS) em runtime; app_migrator so quando rodar migrate
- structlog substituindo print/logging classico (Wave A — observabilidade)
- SECRET_KEY obrigatoria via env (sem default em prod; dev tem fallback no .env)
"""

from pathlib import Path

import environ

# =============================================================
# Paths
# =============================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

# =============================================================
# Seguranca essencial
# =============================================================
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# =============================================================
# Apps
# =============================================================
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_spectacular",
    "django_otp",
    "django_otp.plugins.otp_totp",
]

LOCAL_APPS = [
    # 4 tabelas-nucleo da Foundation F-A (Marco 2 — 2026-05-17)
    "src.infrastructure.tenant.apps.TenantConfig",
    "src.infrastructure.usuario.apps.UsuarioConfig",
    "src.infrastructure.audit.apps.AuditConfig",
    "src.infrastructure.feature_flag.apps.FeatureFlagConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# AUTH_USER_MODEL customizado (Usuario com email como USERNAME_FIELD).
# CRITICO: setado ANTES de qualquer migration — Django nao permite mudar depois.
AUTH_USER_MODEL = "usuario.Usuario"

# =============================================================
# Middleware
# =============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # TenantMiddleware entra no Marco 3 (Multi-tenancy operacional)
    # "src.infrastructure.multitenant.middleware.TenantMiddleware",
]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# =============================================================
# Banco de dados
#
# Conexao runtime usa app_user (NOBYPASSRLS) — defesa em profundidade.
# Migrations rodam via "django.db.backends.postgresql" mas com OPTIONS apontando
# pra DATABASE_MIGRATOR_URL (settings.dev e prod fazem a logica).
# =============================================================
DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "ATOMIC_REQUESTS": True,  # transacao por request — base pra Marco 3
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "application_name": "afere-app",
        },
    },
}

# =============================================================
# Auth / passwords
# =============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# =============================================================
# i18n + tz (memoria: pt-br SP)
# =============================================================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# =============================================================
# Static / media
# =============================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# =============================================================
# Default PK
# =============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================
# DRF + OpenAPI
# =============================================================
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Aferê API (nome do produto provisorio)",
    "DESCRIPTION": (
        "API REST do ERP multi-tenant para assistencia tecnica + calibracao ISO 17025. "
        "Foundation F-A em construcao."
    ),
    "VERSION": "0.1.0-foundation-f-a",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# =============================================================
# Logging — placeholder, structlog completo entra no Marco 4 (audit trail)
# =============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simples": {
            "format": "[{asctime}] {levelname} {name} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simples",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
