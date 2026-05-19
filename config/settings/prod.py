"""Settings de producao — hardening + gate de deploy (FA-M2).

F-A NAO vai pra producao agora (memoria project_deploy_so_quando_roldao_quiser).
Este arquivo herda base e ENDURECE: falha duro (ImproperlyConfigured) se
segredos dedicados ausentes/fracos, e ativa as flags de seguranca de
transporte/cookie. Wave A herda daqui.

FA-A1/FA-M2 (T2 review tech-lead): NAO detectamos "o default inseguro" por
comparacao de valor (`.env` nem e versionado, fragil). Exigimos PROVA
POSITIVA de configuracao — presenca + nao-vazio + piso de entropia.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *
from .base import env

DEBUG = False

# =============================================================
# Gate de deploy — exige conjunto minimo de segredos dedicados
# =============================================================
_secret_key = env("DJANGO_SECRET_KEY", default="")
_pii_key = env("PII_HASH_KEY", default="")
_pii_key_id = env("PII_HASH_KEY_ID", default="")
_allowed = env("DJANGO_ALLOWED_HOSTS", default=[])

if len(_secret_key) < 50:
    raise ImproperlyConfigured(
        "prod: DJANGO_SECRET_KEY ausente ou < 50 chars (entropia insuficiente)."
    )
if len(_pii_key) < 32:
    raise ImproperlyConfigured(
        "prod: PII_HASH_KEY dedicada ausente ou < 32 chars. NAO ha derivacao "
        "de SECRET_KEY em prod (FA-A1: rotacao de SECRET_KEY nao pode "
        "invalidar hash de PII retroativo)."
    )
if not _pii_key_id:
    raise ImproperlyConfigured("prod: PII_HASH_KEY_ID obrigatorio (FA-A1).")
if not _allowed:
    raise ImproperlyConfigured("prod: DJANGO_ALLOWED_HOSTS obrigatorio.")

# =============================================================
# Hardening de transporte / cookies (FA-M2)
# =============================================================
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
# Atras do proxy Hostinger (TLS termina no proxy) — confia no header dele.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# NAO-OBJETIVO: CSP fica fora desta frente (depende de inventario de assets
# da Wave A UI). Logging JSON estruturado entra junto com o deploy.
