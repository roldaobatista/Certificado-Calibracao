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
_qr_key = env("QR_HMAC_KEY", default="")
_qr_key_id = env("QR_HMAC_KEY_ID", default="")
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
# SEC-QR-001 (Marco 2): mesma exigencia de PII — chave dedicada, sem
# derivacao de SECRET_KEY em prod. Hashes QR sobrevivem ate 25 anos
# (RBC cl. 4.2); acoplar a SECRET_KEY = nunca rotacionar SECRET_KEY.
if len(_qr_key) < 32:
    raise ImproperlyConfigured(
        "prod: QR_HMAC_KEY dedicada ausente ou < 32 chars. NAO ha derivacao "
        "de SECRET_KEY em prod (SEC-QR-001: hash de QR fisico sobrevive 25 "
        "anos; rotacao de SECRET_KEY nao pode invalidar etiqueta impressa). "
        "Chave SEPARADA do PII_HASH_KEY — rotacoes desacopladas."
    )
if not _qr_key_id:
    raise ImproperlyConfigured("prod: QR_HMAC_KEY_ID obrigatorio (SEC-QR-001).")
if _qr_key == _pii_key:
    raise ImproperlyConfigured(
        "prod: QR_HMAC_KEY identica a PII_HASH_KEY. Chaves DEVEM ser "
        "distintas — uso e politica de rotacao diferentes (SEC-QR-001)."
    )

# T-EQP-027 (corretora RAT-EQP-QR) — salt do HMAC usado em
# `_hash_ip_simples` (rate-limit QR publico). Salt GLOBAL (nao por
# tenant) porque o rate-limit identifica o mesmo IP cross-tenant.
# Sem gate em prod, o fallback hardcoded vira string publica e o
# espaco IPv4 (~4e9) vira reversivel por brute force em milissegundos
# — atacante reverte ip_hash -> IP e descobre quais IPs visitam quais
# hashes de QR (LGPD art. 5 - IP e dado pessoal). Mesmo padrao gate
# de PII_HASH_KEY + QR_HMAC_KEY.
_qr_ip_salt = env("QR_IP_RATELIMIT_SALT", default="")
if len(_qr_ip_salt) < 32:
    raise ImproperlyConfigured(
        "prod: QR_IP_RATELIMIT_SALT ausente ou < 32 chars. Salt do "
        "HMAC de ip_hash do rate-limit do QR publico — sem ele, espaco "
        "IPv4 vira reversivel por brute force (corretora RAT-EQP-QR). "
        "Rotacao mensal Wave A; usar string >=32 chars random hex."
    )
if _qr_ip_salt == _qr_key or _qr_ip_salt == _pii_key:
    raise ImproperlyConfigured(
        "prod: QR_IP_RATELIMIT_SALT identico a outra chave de seguranca. "
        "Chaves DEVEM ser distintas — uso e politica de rotacao diferentes."
    )

if not _allowed:
    raise ImproperlyConfigured("prod: DJANGO_ALLOWED_HOSTS obrigatorio.")

ALLOWED_HOSTS = _allowed

# =============================================================
# Hardening de transporte / cookies (FA-M2 + F-C1 P3 retrofit R-1)
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

# =============================================================
# F-C1 P3 retrofit (R-1 / TL-01 — settings expandidos)
# =============================================================
# Referrer Policy — limita vazamento de URL atraves do Referer header.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# CSRF Trusted Origins — exige declaracao explicita; sem isso, POST cross-site
# de qualquer dominio dispara CsrfViewMiddleware reject.
# Hostinger + Cloudflare colocam o app atras de proxy; os hosts confiaveis
# (mesmos do ALLOWED_HOSTS com prefixo https) entram aqui.
CSRF_TRUSTED_ORIGINS = env(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[f"https://{host}" for host in _allowed if host and host != "*"],
)
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured(
        "prod: CSRF_TRUSTED_ORIGINS vazio (deriva de DJANGO_ALLOWED_HOSTS — "
        "verifique que ALLOWED_HOSTS tem >=1 host valido)."
    )

# Anti-DoS form bomb (TL-01 / R-1): limita tamanho de upload em memoria e
# numero de campos por request. Defaults Django sao generosos (2.5MB / 1000)
# — apertamos pra 10MB / 1000 explicitos no prod.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10_485_760  # 10 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
# FILE_UPLOAD_MAX_MEMORY_SIZE mantem default Django (2.5MB) — uploads
# grandes vao pra disco temporario, nao a memoria.

# Content Security Policy (R-1 / TL-01): nivel minimo restritivo —
# default-src 'self' + bloqueio de inline scripts. Wave A UI vai
# ajustar quando inventario de assets externos for definido (CDNs,
# fontes, etc). Ate la, qualquer recurso externo precisa ADR.
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ("'self'",),
        "script-src": ("'self'",),
        "style-src": ("'self'", "'unsafe-inline'"),  # HTMX swap injeta style inline
        "img-src": ("'self'", "data:"),
        "font-src": ("'self'",),
        "connect-src": ("'self'",),
        "frame-ancestors": ("'none'",),  # complementa X-Frame-Options DENY
        "form-action": ("'self'",),
        "base-uri": ("'self'",),
        "object-src": ("'none'",),
    },
}
# django-csp 4.0+ usa setting unica acima. MIDDLEWARE ja foi configurado
# em base.py se django-csp estiver instalado; aqui so a politica.

# NAO-OBJETIVO: logging JSON estruturado entra junto com a Foundation F-C2
# (observabilidade infra — structlog + middleware HTTP correlation_id +
# processor automatico tenant_id/correlation_id/request_id).
