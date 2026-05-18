"""Settings de teste — overlay de base.py.

Pra pytest local + CI: NAO depende de Redis (LocMemCache override em CACHES).
- Redis fica reservado pra `dev.py` (rodando em docker-compose) e `prod.py`.
- LocMemCache em test e seguro porque cada test_case roda em transacao isolada
  e nao precisa compartilhar cache entre workers (pytest-xdist ainda nao usado).

Decisao 2026-05-18 noite, pos-review tech-lead US-EQP-003 (Redis no dev/prod;
LocMem em test pra nao acoplar CI a container externo).
"""

from .base import *  # noqa: F401,F403

# Sobrescreve cache Redis -> LocMem em testes.
# Memoria `feedback_nao_declarar_pronto_sem_rodar`: testes precisam rodar isolados.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "afere-test-cache",
    },
    "ratelimit": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "afere-test-ratelimit",
    },
}

# Senha hasher mais rapido em test (default eh argon2 — 100x mais lento).
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# DEBUG False em test pra forcar comportamento de producao em erros.
DEBUG = False
