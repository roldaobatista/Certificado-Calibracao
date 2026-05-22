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

import time
from typing import ClassVar

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


def _resposta_404_indistinguivel(inicio_perf: float) -> Response:
    """404 padrao (P-EQP-S2 + AC-EQP-003-3). Caller chama timing
    constant ANTES de retornar para alinhar latencia."""
    aplicar_timing_constant_se_necessario(inicio_perf)
    return Response(
        {"detail": "qr_nao_encontrado"},
        status=status.HTTP_404_NOT_FOUND,
    )


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
    def get(self, request: Request, hash: str) -> Response:
        inicio_perf = time.perf_counter()

        # Path publico — middleware nao seta active_tenant. Se sessao
        # autenticada + header X-Afere-Active-Tenant, tenta Escopo A
        # setando context manualmente. Sem header ou sem auth -> C.
        if request.user.is_authenticated:
            from uuid import UUID

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
                    return _resposta_404_indistinguivel(inicio_perf)
                # Reabre contexto para construir ficha (le versoes,
                # certificados, etc — RLS aplica).
                with run_in_tenant_context(tenant_id):
                    ficha = construir_ficha_360(qrcode.equipamento)
                aplicar_timing_constant_se_necessario(inicio_perf)
                return Response(ficha, status=status.HTTP_200_OK)
            # Sem header de tenant ativo: trata como Escopo C
            # (autenticado mas sem context — fallback seguro).

        # Escopo C (anonimo): SECURITY DEFINER ignora RLS controladamente,
        # retorna allowlist minima.
        resolvido = resolver_escopo_c_anonimo(hash)
        if resolvido is None:
            return _resposta_404_indistinguivel(inicio_perf)
        aplicar_timing_constant_se_necessario(inicio_perf)
        return Response(resolvido.payload, status=status.HTTP_200_OK)


qr_publico_view = QRPublicoView.as_view()
