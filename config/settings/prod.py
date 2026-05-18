"""Settings de producao — placeholder.

F-A NAO vai pra producao (memoria project_deploy_so_quando_roldao_quiser).
Este arquivo existe pra mypy nao reclamar e pra Wave A herdar daqui.
Hardening de prod (CSP, HSTS, secure cookies, etc) entra quando Roldao
autorizar deploy.
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# Configuracoes obrigatorias quando Roldao autorizar deploy:
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = "DENY"
# CSP_DEFAULT_SRC = ("'self'",)

# Logging estruturado JSON pra Grafana Cloud + Axiom (ADR-0001)
# completo entra junto com o deploy.
