"""AdminHardeningMiddleware — INV-ADMIN-001/002/003 (F-C1 P4 T-FC1-04+07).

Defesa em 4 camadas pra /admin/* :

1. MFA TOTP verificado (via django-otp `is_verified()`) nas ultimas 8h.
   Reusa fluxo F-B; aqui so verifica que esta valido.
2. IP allowlist (env var ADMIN_IP_ALLOWLIST com lista CIDR).
3. Rate-limit 5 tentativas/IP/15min em login (cache backend, atras de Redis
   em F-C3; ate la, LocMemCache — note `auditor-performance` PERF-3
   acknowledged isso vira teatro multi-worker; aceito ate F-C3).
4. Session-rebind (AC-FC1-002-8 / R-9 / TL-06): no login admin, grava
   `session['admin_ip_hash']` + `session['admin_ua_hash']`. Mismatch em
   request seguinte -> 403 + invalida sessao.

Tudo registrado em tabela `audit_trail.admin_access` (T-FC1-05).

SEC-LOG-001 — 403 SEMPRE igual (sem oracle de qual camada falhou).
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import logging
import os
import time
from collections.abc import Callable

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

ADMIN_PATH_PREFIX = "/admin/"
ADMIN_LOGIN_PATH = "/admin/login/"
ADMIN_LOGOUT_PATH = "/admin/logout/"

RATE_LIMIT_TENTATIVAS = 5
RATE_LIMIT_JANELA_SEG = 15 * 60  # 15min
RATE_LIMIT_LOCKOUT_SEG = 60 * 60  # 1h

MFA_JANELA_MAX_SEG = 8 * 60 * 60  # 8h


def _hash_ip(ip: str) -> str:
    """HMAC-SHA256 do IP com salt versionado (anti-reversao por brute force
    no espaco IPv4 ~4e9; mesma tecnica do `_hash_ip_simples` do QR public)."""
    salt = (
        getattr(settings, "ADMIN_ACCESS_HASH_SALT", None)
        or os.environ.get("ADMIN_ACCESS_HASH_SALT", "")
    )
    if not salt:
        # Em prod, settings forca via gate (ImproperlyConfigured). Em dev,
        # fallback nao-vazio pra middleware nao quebrar.
        salt = "dev-only-fallback-admin-ip-salt"
    return hmac.new(salt.encode("utf-8"), ip.encode("utf-8"), hashlib.sha256).hexdigest()


def _hash_ua(user_agent: str) -> str:
    """Mesmo salt do _hash_ip (LGPD: UA tambem e PII indireta)."""
    return _hash_ip(user_agent)


def _ip_do_request(request: HttpRequest) -> str:
    """Extrai IP do header X-Forwarded-For (Hostinger/Cloudflare atras de
    proxy). Pega o ULTIMO IP da cadeia (o que o proxy validou); fallback
    REMOTE_ADDR direto.

    Cuidado classico: nao confiar no PRIMEIRO IP do XFF (pode ser
    spoofado pelo cliente). Em prod com SECURE_PROXY_SSL_HEADER, o Django
    ja faz isso certo via `request.META`."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        # Pega o ULTIMO (mais proximo do app)
        return xff.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _ip_no_allowlist(ip: str) -> bool:
    """Verifica se IP esta na env var ADMIN_IP_ALLOWLIST (lista CIDR
    separada por virgula). Vazio = recusa tudo (default seguro)."""
    allowlist_raw = (
        getattr(settings, "ADMIN_IP_ALLOWLIST", None)
        or os.environ.get("ADMIN_IP_ALLOWLIST", "")
    )
    if not allowlist_raw:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for cidr in allowlist_raw.split(","):
        cidr_clean = cidr.strip()
        if not cidr_clean:
            continue
        try:
            rede = ipaddress.ip_network(cidr_clean, strict=False)
            if addr in rede:
                return True
        except ValueError:
            continue
    return False


def _registrar_acesso_admin(
    *,
    request: HttpRequest,
    status_code: int,
    motivo_negacao: str | None,
    eh_break_glass: bool,
) -> None:
    """Grava entrada em audit_trail.admin_access.

    Lazy import do model pra evitar circular at module load. Tabela criada
    em audit/migrations/0017 (T-FC1-05). Se a tabela ainda nao existe (dev
    sem migrate), captura silencioso e segue (NAO bloqueia request).
    """
    try:
        # Lazy import — model criado em T-FC1-05
        from src.infrastructure.audit.models import AdminAccess  # type: ignore[attr-defined]
    except ImportError:
        return
    try:
        ip = _ip_do_request(request)
        user = getattr(request, "user", None)
        usuario_id = (
            user.id if user and getattr(user, "is_authenticated", False) else None
        )
        AdminAccess.objects.create(
            usuario_id=usuario_id,
            ip_hash=_hash_ip(ip),
            user_agent_hash=_hash_ua(request.META.get("HTTP_USER_AGENT", "")),
            path=request.path[:500],
            metodo=request.method[:10],
            status_code=status_code,
            motivo_negacao=motivo_negacao or "",
            eh_break_glass=eh_break_glass,
        )
    except Exception:
        logger.exception("Falha gravando admin_access (nao-bloqueante)")


class AdminHardeningMiddleware(MiddlewareMixin):
    """4 camadas de defesa pra /admin/*."""

    def process_request(self, request: HttpRequest) -> HttpResponse | None:
        path = request.path
        # So aplica em /admin/*
        if not path.startswith(ADMIN_PATH_PREFIX):
            return None
        # Login e logout: passa pra view, mas aplica rate-limit antes
        ip = _ip_do_request(request)

        # ---- Camada 3: rate-limit (pre-auth pra anti-brute-force) ----
        # Aplica nas tentativas POST de login. GETs do form passam.
        if path == ADMIN_LOGIN_PATH and request.method == "POST":
            chave_cache = f"admin_login_attempts:{_hash_ip(ip)}"
            tentativas = cache.get(chave_cache, 0)
            if tentativas >= RATE_LIMIT_TENTATIVAS:
                _registrar_acesso_admin(
                    request=request,
                    status_code=403,
                    motivo_negacao="rate_limit",
                    eh_break_glass=False,
                )
                return HttpResponseForbidden()
            # Incrementa antes do request (defesa pessimista)
            cache.set(chave_cache, tentativas + 1, RATE_LIMIT_JANELA_SEG)

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            # Anonimo no /admin/* (exceto login GET): nega
            if path not in (ADMIN_LOGIN_PATH, ADMIN_LOGOUT_PATH):
                _registrar_acesso_admin(
                    request=request,
                    status_code=403,
                    motivo_negacao="anonimo",
                    eh_break_glass=False,
                )
                return HttpResponseForbidden()
            return None  # GET de login passa

        # ---- Detecta conta break-glass (US-FC1-006) ----
        eh_break_glass = bool(getattr(user, "is_break_glass", False))

        # ---- Camada 2: IP allowlist ----
        # Break-glass tem allowlist propria (mais permissiva — dispara alerta)
        if not eh_break_glass and not _ip_no_allowlist(ip):
            _registrar_acesso_admin(
                request=request,
                status_code=403,
                motivo_negacao="ip_fora_allowlist",
                eh_break_glass=False,
            )
            return HttpResponseForbidden()

        # ---- Camada 1: MFA verificado (django-otp) ----
        # Break-glass usa U2F (verificacao especifica em T-FC1-13).
        # Normal: exige is_verified() do django-otp + janela 8h.
        is_verified = getattr(user, "is_verified", lambda: False)()
        if not is_verified:
            _registrar_acesso_admin(
                request=request,
                status_code=403,
                motivo_negacao="mfa_nao_verificado",
                eh_break_glass=eh_break_glass,
            )
            return HttpResponseForbidden()

        # ---- Camada 4: session-rebind (AC-FC1-002-8) ----
        ip_hash_atual = _hash_ip(ip)
        ua_hash_atual = _hash_ua(request.META.get("HTTP_USER_AGENT", ""))
        ip_hash_sessao = request.session.get("admin_ip_hash")
        ua_hash_sessao = request.session.get("admin_ua_hash")

        if ip_hash_sessao is None:
            # 1o request admin desta sessao: grava
            request.session["admin_ip_hash"] = ip_hash_atual
            request.session["admin_ua_hash"] = ua_hash_atual
            request.session["admin_login_em"] = int(time.time())
        else:
            # Sessao subsequente: valida match
            if (
                not hmac.compare_digest(ip_hash_sessao, ip_hash_atual)
                or not hmac.compare_digest(ua_hash_sessao or "", ua_hash_atual)
            ):
                _registrar_acesso_admin(
                    request=request,
                    status_code=403,
                    motivo_negacao="session_rebind_mismatch",
                    eh_break_glass=eh_break_glass,
                )
                request.session.flush()
                return HttpResponseForbidden()

        # ---- Janela MFA 8h ----
        login_em = request.session.get("admin_login_em", 0)
        if int(time.time()) - login_em > MFA_JANELA_MAX_SEG:
            _registrar_acesso_admin(
                request=request,
                status_code=403,
                motivo_negacao="mfa_janela_expirada",
                eh_break_glass=eh_break_glass,
            )
            request.session.flush()
            return HttpResponseForbidden()

        # ---- Sucesso: registra acesso ----
        _registrar_acesso_admin(
            request=request,
            status_code=200,  # placeholder; view real pode mudar
            motivo_negacao=None,
            eh_break_glass=eh_break_glass,
        )
        return None
