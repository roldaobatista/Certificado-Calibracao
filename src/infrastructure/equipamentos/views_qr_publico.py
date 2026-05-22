"""View publica GET `/api/v1/qr/{hash}/` (T-EQP-025+026+033 / US-EQP-003).

3 escopos (INV-051 + RBC B6 + P-EQP-S2):
- Escopo A (autenticado + mesmo tenant do equipamento) → 200 ficha
  completa (reusa `construir_ficha_360`).
- Escopo B (autenticado + outro tenant) → 404 indistinguivel
  (P-EQP-S2; sem oracle cross-tenant).
- Escopo C (anonimo) → 200 payload minimo allowlist.

Hash invalido / revogado / inexistente → 404 indistinguivel.

Timing constant (AC-EQP-003-3 / P-EQP-T3): tempo total normalizado
para `TIMING_ALVO_MS` (200ms) via `aplicar_timing_constant_se_necessario`.

Implementacao via APIView CBV + `PublicEndpoint` mixin (FB-C2 unico
canal) + `permission_classes = []` para sobrescrever IsAuthenticated
global. View func decorated nao propaga atributo `_authz_public` por
causa do wrapping do `@api_view`.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import ClassVar
from uuid import UUID

from django.conf import settings
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from src.infrastructure.authz.decorators import PublicEndpoint
from src.infrastructure.equipamentos.services_ficha360 import construir_ficha_360
from src.infrastructure.equipamentos.services_qr_publico import (
    aplicar_timing_constant_se_necessario,
    resolver_escopo_a_se_mesmo_tenant,
    resolver_escopo_c_anonimo,
)
from src.infrastructure.equipamentos.services_ratelimit import (
    avaliar_limite_ip,
    avaliar_limite_tenant_qr,
    registrar_4xx_ip,
)

# T-EQP-027 — IP hash usa SALT GLOBAL dedicado ao rate-limit (escopo
# trans-tenant; salt por tenant nao serve pois o rate-limit precisa
# identificar o mesmo IP cross-tenant). HMAC defende contra rainbow
# table. Em prod, gate em config/settings/prod.py exige >=32 chars
# + distincao de QR_HMAC_KEY/PII_HASH_KEY (corretora RAT-EQP-QR).
# Wave A: rotacao mensal do salt + KMS.
_IP_SALT_QR_RATELIMIT = settings.QR_IP_RATELIMIT_SALT.encode("utf-8")


def _hash_ip_simples(ip: str) -> str:  # audit-pii-salt: skip -- rate-limit cross-tenant exige salt GLOBAL (nao por tenant); HMAC com `_IP_SALT_QR_RATELIMIT` protege contra rainbow table; rotacao mensal Wave A
    """HMAC-SHA256 com salt global truncado a 32 chars hex (128 bits).

    Salt global (NAO por tenant) porque o rate-limit precisa
    identificar o mesmo IP cross-tenant + anonimo. Override no
    audit-pii-salt-check justificado: mesmo IP em 2 tenants tem que
    bater na mesma chave de cache; salt por tenant inviabilizaria isso.
    """
    if not ip:
        return ""
    return hmac.new(
        _IP_SALT_QR_RATELIMIT, ip.encode("utf-8"), hashlib.sha256
    ).hexdigest()[:32]


def _extrair_ip(request: Request) -> str:
    """X-Forwarded-For (primeiro IP) ou REMOTE_ADDR."""
    return (
        request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        or request.META.get("REMOTE_ADDR", "")
    )


def _resposta_404_indistinguivel(
    inicio_perf: float, ip_hash: str = ""
) -> Response:
    """404 padrao (P-EQP-S2 + AC-EQP-003-3). Caller chama timing
    constant ANTES de retornar para alinhar latencia.

    Quando `ip_hash` presente, conta como 4xx no rate-limit (T-EQP-027).
    """
    if ip_hash:
        registrar_4xx_ip(ip_hash)
    aplicar_timing_constant_se_necessario(inicio_perf)
    return Response(
        {"detail": "qr_nao_encontrado"},
        status=status.HTTP_404_NOT_FOUND,
    )


def _resposta_429(retry_after: int, motivo: str) -> Response:
    """429 com `Retry-After` (T-EQP-027 / T-EQP-032)."""
    resp = Response(
        {"detail": "rate_limit_excedido", "motivo": motivo},
        status=status.HTTP_429_TOO_MANY_REQUESTS,
    )
    resp["Retry-After"] = str(int(retry_after))
    return resp


def _contar_equipamentos_ativos_tenant(tenant_id: UUID) -> int:
    """Conta equipamentos ativos do tenant pra computar limite global
    (T-EQP-032). Cache 5min — saturacao por tenant nao muda em segundos.
    """
    from django.core.cache import caches

    from src.infrastructure.equipamentos.models import Equipamento
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    cache = caches["ratelimit"]
    chave = f"qr:tnt:eqp_ativos:{tenant_id}"
    valor = cache.get(chave)
    if valor is not None:
        return int(valor)
    with run_in_tenant_context(tenant_id):
        contagem = Equipamento.objects.filter(deletado_em__isnull=True).count()
    cache.set(chave, contagem, 300)
    return contagem


# authz-check: skip -- endpoint PUBLICO (escopo C); RBC B6 + INV-051 +
# allowlist canonica em qr-publico-allowlist.md. PublicEndpoint marca
# via helper unico FB-C2 (RequireAuthz reconhece via is_public).
class QRPublicoView(PublicEndpoint, APIView):
    """GET `/api/v1/qr/{hash}/` — resolve em 3 escopos com latencia
    constante.

    Sem authentication_classes (vazio override) — Escopo C anonimo.
    Sem permission_classes (vazio override) — IsAuthenticated global
    nao se aplica. RequireAuthz reconhece via PublicEndpoint
    (_authz_public = True).
    """

    # SessionAuthentication preservada para detectar Escopo A
    # (usuario autenticado). Mas permission_classes vazio significa que
    # acesso anonimo (Escopo C) tambem passa — sem permissao bloqueando.
    authentication_classes: ClassVar[list] = [SessionAuthentication]
    permission_classes: ClassVar[list] = []

    # authz-check: skip -- endpoint PUBLICO via PublicEndpoint mixin;
    # RBC B6 + INV-051. Escopo A retorna ficha completa via RLS (mesmo
    # tenant); B/C/invalido -> 404 indistinguivel ou allowlist publica.
    # authz-check: skip -- endpoint PUBLICO via PublicEndpoint mixin (RBC B6 + INV-051).
    def get(self, request: Request, hash: str) -> Response:
        inicio_perf = time.perf_counter()

        # T-EQP-027 — rate-limit por IP (60/min + lockout 24h apos
        # 100 4xx/h). Aplica ANTES de qualquer resolucao para evitar
        # uso da view como oraculo de validade do hash.
        ip = _extrair_ip(request)
        ip_hash = _hash_ip_simples(ip)
        avaliacao_ip = avaliar_limite_ip(ip_hash)
        if not avaliacao_ip.permitido:
            return _resposta_429(
                avaliacao_ip.retry_after_seg,
                motivo=avaliacao_ip.motivo,
            )

        # Path publico — middleware nao seta active_tenant. Se sessao
        # autenticada + header X-Afere-Active-Tenant, tenta Escopo A
        # setando context manualmente. Sem header ou sem auth -> C.
        if request.user.is_authenticated:
            from src.infrastructure.multitenant.connection import (
                run_in_tenant_context,
            )

            tenant_hdr = request.META.get("HTTP_X_AFERE_ACTIVE_TENANT", "")
            tenant_id: UUID | None = None
            if tenant_hdr:
                try:
                    tenant_id = UUID(tenant_hdr)
                except ValueError:
                    tenant_id = None
            if tenant_id is not None:
                with run_in_tenant_context(tenant_id):
                    qrcode = resolver_escopo_a_se_mesmo_tenant(hash)
                if qrcode is None:
                    # Escopo B (autenticado outro tenant) OU hash invalido
                    # OU revogado/inexistente — 404 indistinguivel.
                    return _resposta_404_indistinguivel(inicio_perf, ip_hash)
                # T-EQP-032 — rate-limit global por tenant para Escopo A.
                n_equip = _contar_equipamentos_ativos_tenant(qrcode.tenant_id)
                avaliacao_tnt = avaliar_limite_tenant_qr(
                    tenant_id=qrcode.tenant_id,
                    n_equipamentos_ativos=n_equip,
                )
                if not avaliacao_tnt.permitido:
                    return _resposta_429(
                        retry_after=24 * 3600,
                        motivo=avaliacao_tnt.motivo,
                    )
                # Reabre contexto para construir ficha (le versoes,
                # certificados, etc — RLS aplica).
                with run_in_tenant_context(tenant_id):
                    ficha = construir_ficha_360(
                        qrcode.equipamento,
                        usuario_id=request.user.id,
                    )
                aplicar_timing_constant_se_necessario(inicio_perf)
                return Response(ficha, status=status.HTTP_200_OK)
            # Sem header de tenant ativo: trata como Escopo C
            # (autenticado mas sem context — fallback seguro).

        # Escopo C (anonimo): SECURITY DEFINER ignora RLS controladamente,
        # retorna allowlist minima.
        resolvido = resolver_escopo_c_anonimo(hash)
        if resolvido is None:
            return _resposta_404_indistinguivel(inicio_perf, ip_hash)
        # T-EQP-032 — rate-limit global por tenant do equipamento (escopo
        # anonimo). resolver_escopo_c_anonimo devolve tenant_id do dono.
        n_equip = _contar_equipamentos_ativos_tenant(resolvido.tenant_id)
        avaliacao_tnt = avaliar_limite_tenant_qr(
            tenant_id=resolvido.tenant_id,
            n_equipamentos_ativos=n_equip,
        )
        if not avaliacao_tnt.permitido:
            return _resposta_429(
                retry_after=24 * 3600,
                motivo=avaliacao_tnt.motivo,
            )
        aplicar_timing_constant_se_necessario(inicio_perf)
        return Response(resolvido.payload, status=status.HTTP_200_OK)


qr_publico_view = QRPublicoView.as_view()
