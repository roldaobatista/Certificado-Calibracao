"""Settings base compartilhados entre dev e prod.

Decisoes:
- pt-br + America/Sao_Paulo (memoria projeto convencoes)
- Argon2 como primeiro password hasher (resistente a GPU/ASIC)
- Conexao app_user (NOBYPASSRLS) em runtime; app_migrator so quando rodar migrate
- structlog substituindo print/logging classico (Wave A — observabilidade)
- SECRET_KEY obrigatoria via env (sem default em prod; dev tem fallback no .env)
"""

import hashlib
import os
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

# Chave server-side pra HMAC de PII em audit (SANEA-02 + FA-A1). O hash de
# CPF/CNPJ/IP NAO pode ser derivavel do tenant_id (publico) — HMAC com chave
# secreta de servidor torna irreversivel sem a chave (pseudonimizacao, NAO
# anonimizacao — R3 advogado FA-A1).
#
# FA-A1: chave VERSIONADA. Antes a chave derivava de SECRET_KEY se env vazia;
# rotacionar SECRET_KEY (boa pratica) invalidava TODOS os hashes retroativos
# => impossivel responder ANPD "quem viu CPF X em data Y". Agora:
#   - PII_HASH_KEY_ID: id da chave ATIVA (default "v1").
#   - PII_HASH_KEY: segredo cru da chave ativa.
#   - PII_HASH_KEYS_RETIRED: "v0:seg0,v-1:segX" — chaves aposentadas, so pra
#     VERIFICAR hashes antigos apos rotacao (prestacao de contas art. 37).
#   - Fallback derivado de SECRET_KEY so FORA de prod (dev/test). prod.py
#     proibe (FA-M2: ImproperlyConfigured).
# Registry encapsulado: __repr__/__str__ redatados pra NAO vazar segredo via
# `manage.py diffsettings` / error report 500 (T1 BLOQUEANTE tech-lead).


class _RegistroChavesPII:
    """Cofre de chaves de HMAC de PII. Nunca expoe bytes em repr/str/log."""

    def __init__(self, ativa_id: str, chaves: dict[str, bytes]) -> None:
        if ativa_id not in chaves:
            raise ValueError(f"PII_HASH_KEY_ID={ativa_id!r} ausente do registry de chaves")
        self._ativa_id = ativa_id
        self._chaves = chaves

    @property
    def ativa_id(self) -> str:
        return self._ativa_id

    def chave_ativa(self) -> bytes:
        return self._chaves[self._ativa_id]

    def chave(self, key_id: str) -> bytes:
        """Bytes da chave `key_id` (ativa ou aposentada). KeyError se ausente."""
        return self._chaves[key_id]

    def tem(self, key_id: str) -> bool:
        return key_id in self._chaves

    def __repr__(self) -> str:
        return (
            f"<RegistroChavesPII: ids={sorted(self._chaves)} "
            f"ativa={self._ativa_id!r} (redacted)>"
        )

    __str__ = __repr__


def _parse_chaves_aposentadas(bruto: str) -> dict[str, bytes]:
    """Parseia "v0:seg0,v-1:segX". Malformado => ValueError (nunca silencio).

    String inteira vazia => {} (sem chaves aposentadas — caso normal). Mas
    token vazio entre vírgulas ("v0:s,,v1:t" / vírgula final) é malformado e
    levanta (T2 tech-lead: nunca silenciar config torta).
    """
    chaves: dict[str, bytes] = {}
    if not bruto.strip():
        return chaves
    for par in (p.strip() for p in bruto.split(",")):
        if not par:
            raise ValueError(
                "PII_HASH_KEYS_RETIRED malformado: token vazio " "(virgula dupla/final)"
            )
        kid, sep, seg = par.partition(":")
        kid, seg = kid.strip(), seg.strip()
        if not sep or not kid or not seg:
            raise ValueError(f"PII_HASH_KEYS_RETIRED malformado: {par!r} (esperado 'id:segredo')")
        chaves[kid] = seg.encode("utf-8")
    return chaves


PII_HASH_KEY_ID: str = env("PII_HASH_KEY_ID", default="v1")
_pii_hash_key_env = env("PII_HASH_KEY", default="")
_pii_chave_ativa: bytes = (
    _pii_hash_key_env.encode("utf-8")
    if _pii_hash_key_env
    else hashlib.sha256(f"afere-pii-hmac-v1:{SECRET_KEY}".encode()).digest()
)
_pii_chaves: dict[str, bytes] = {
    **_parse_chaves_aposentadas(env("PII_HASH_KEYS_RETIRED", default="")),
    PII_HASH_KEY_ID: _pii_chave_ativa,
}
PII_HASH_KEY_REGISTRO = _RegistroChavesPII(PII_HASH_KEY_ID, _pii_chaves)

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
    # Multi-tenancy operacional (Marco 3 — 2026-05-17): middleware + RLS policies
    "src.infrastructure.multitenant.apps.MultitenantConfig",
    # Autorizacao (Foundation F-B — 2026-05-18): porta + RBAC + audit synchronous
    "src.infrastructure.authz.apps.AuthzConfig",
    # Wave A Marco 1 — Clientes (comercial). PF/PJ + dedup INV-024 + CNPJ alfanumerico.
    "src.infrastructure.clientes.apps.ClientesConfig",
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
    # Marco 3: depois de AuthenticationMiddleware (precisa de request.user).
    # Trava de isolamento entre clientes — bypass automatico de /healthz/, /admin/,
    # /api/schema/, /api/docs/, /static/, /media/. Detalhes em middleware.py.
    "src.infrastructure.multitenant.middleware.TenantMiddleware",
    # F-B: enforcement MFA TOTP pros perfis sensiveis (SEC-MFA-001).
    # Depois de TenantMiddleware (le active_tenant_context).
    "src.infrastructure.authz.middleware.MfaRequiredMiddleware",
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
# Banco de dados — 2 alias com roles distintas (ADR-0002 §2)
#
# default  → app_user      (NOBYPASSRLS, runtime do app + workers)
# migrator → app_migrator  (NOBYPASSRLS, apenas DDL — migrate/makemigrations)
#
# Router em src/infrastructure/multitenant/router.py manda allow_migrate
# apenas pro alias `migrator`. Comando: `manage.py migrate --database=migrator`.
# =============================================================
DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "application_name": "afere-app-runtime",
        },
        # pytest-django reusa este DB em testes. Nome fixo evita prefixacao
        # automatica 'test_' que confunde quando temos 2 alias apontando
        # pro mesmo banco fisico de teste.
        "TEST": {"NAME": "test_afere", "MIGRATE": True},
    },
    "migrator": {
        **env.db("DATABASE_MIGRATOR_URL"),
        "ATOMIC_REQUESTS": False,
        "CONN_MAX_AGE": 0,
        "OPTIONS": {
            "application_name": "afere-app-migrator",
        },
        # Em teste, migrator aponta pro MESMO banco que default — o test
        # database. Sem isso, migrate corre contra o DB de prod.
        "TEST": {"NAME": "test_afere", "MIGRATE": True, "DEPENDENCIES": []},
    },
}

DATABASE_ROUTERS = ["src.infrastructure.multitenant.router.TenantMultiRoleRouter"]

# =============================================================
# Auth / passwords
# =============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
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
    # F-B: deny-by-default — toda view DRF precisa declarar `authz_action`
    # OU `authz_public = True`. INV-AUTHZ-001 cravada na borda.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "src.infrastructure.authz.permissions.RequireAuthz",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# Cache:
# - Default: Redis (Wave A Marco 2 — decisao Roldao 2026-05-18 noite apos review tech-lead US-EQP-003).
#   Razao: rate-limit por IP em multi-worker (django-ratelimit funciona com Redis, nao com
#   LocMemCache que e per-process), idempotency_keys (US-EQP-004/005), cache compartilhado
#   da ficha 360 quando p95 estourar (RBC C5).
# - Fallback LocMem: settings/test.py override pra testes sem dependencia externa.
# Override seguro via env var REDIS_URL.
_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": _REDIS_URL,
        "OPTIONS": {
            "db": "1",  # DB 1 para cache geral
        },
        "KEY_PREFIX": "afere",
    },
    "ratelimit": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": _REDIS_URL,
        "OPTIONS": {
            "db": "2",  # DB 2 isolado para rate-limit (TTLs curtos, alta rotatividade)
        },
        "KEY_PREFIX": "afere-rl",
    },
}

# =============================================================
# Upload limites (US-CLI-003 R1 tech-lead — DoS) — 2 MiB suficiente pra ~10000
# linhas CSV razoaveis; 1000 linhas reais cabem em ~150 KiB.
# Excedido => 413 estruturada na view; nao consome mais que isto na memoria
# antes do parser cortar.
# =============================================================
_MIB = 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * _MIB
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * _MIB
# Quantidade de campos de formulario (defesa adicional contra hash-collision DoS).
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

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
