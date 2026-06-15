"""Webhook público de baixa automática de cobrança — ContasReceberWebhookView (T-CR-036).

POST /api/v1/public/contas-receber/webhook/

SEM autenticação (HMAC = autorização). O gateway_externo_id resolve o tenant SEM RLS via
`resolver_cr_titulo_por_gateway` (migration 0006 — SECURITY DEFINER); depois a view entra
em `run_in_tenant_context(tenant_id)` e o resto roda sob RLS normal.

Segurança (D-CR-8 / R7 / INV-FIN-GW-001):
  - Rate-limit por IP (30 req/min — molde views_publicas.py orcamentos).
  - HMAC validado pelo provider ANTES de qualquer operação de escrita.
  - Anti-oráculo: gateway_id inexistente ≡ HMAC inválido = 401 IGUAL (mesmo corpo, sem
    distinção — D-CR-8 / R7). Timing real = GATE-CR-ASAAS (pentest pré-produção).
  - Idempotência dupla: gateway_event_id (INSERT-check) + estado pago (no-op).
  - Baixa + INSERT evento WORM + publicar_evento na MESMA transaction.atomic.
  - INV-CR-WEBHOOK-PAYLOAD-MINIMO: handler NÃO persiste/loga PII do pagador
    além do que Pagamento precisa (D-CR-19).

GATE-CR-ASAAS: HMAC real Asaas + pentest = pré-produção. Wave A usa Mock.

# authz-check: skip -- endpoint PUBLICO via PublicEndpoint mixin (HMAC = autorização, D-CR-8)
"""

from __future__ import annotations

import hashlib
import hmac as _hmac_module
import logging
from typing import Any
from uuid import UUID

from django.db import transaction
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from src.application.contas_receber import processar_webhook_pagamento
from src.domain.contas_receber.erros import WebhookHMACInvalido
from src.domain.contas_receber.portas import PaymentGatewayProvider
from src.infrastructure.authz.decorators import PublicEndpoint
from src.infrastructure.contas_receber.repositories import DjangoTituloRepository
from src.infrastructure.multitenant.connection import run_in_tenant_context

logger = logging.getLogger(__name__)

_WEBHOOK_LIMITE_REQ_MIN = 30
_WEBHOOK_JANELA_SEG = 60


# audit-pii-salt: skip -- HMAC IP rate-limit cross-tenant; salt global CR_WEBHOOK_IP_RATELIMIT_SALT; molde QR/ORC
def _webhook_hash_ip(ip: str) -> str:
    """HMAC-SHA256 do IP com salt global (rate-limit webhook cross-tenant). '' se vazio."""
    from django.conf import settings as _settings

    salt_str = getattr(_settings, "CR_WEBHOOK_IP_RATELIMIT_SALT", "dev-only-cr-webhook")
    salt = salt_str.encode("utf-8")
    if not ip:
        return ""
    return _hmac_module.new(salt, ip.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _webhook_extrair_ip(request: Request) -> str:
    forwarded = str(request.META.get("HTTP_X_FORWARDED_FOR", "") or "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return str(request.META.get("REMOTE_ADDR", "") or "")


def _webhook_rate_limit_ok(ip_hash: str) -> bool:
    """30 req/min/IP (janela fixa). True se permitido."""
    if not ip_hash:
        return True
    from django.core.cache import caches

    cache = caches["ratelimit"]
    chave = f"cr:webhook:ip:{ip_hash}"
    cache.add(chave, 0, _WEBHOOK_JANELA_SEG)
    try:
        contagem = cache.incr(chave)
    except ValueError:
        cache.set(chave, 1, _WEBHOOK_JANELA_SEG)
        contagem = 1
    return contagem <= _WEBHOOK_LIMITE_REQ_MIN


def _resolver_cr_titulo_por_gateway(gateway_id: str) -> tuple[UUID, UUID] | None:
    """Chama a função SECURITY DEFINER para resolver (tenant_id, titulo_id) sem RLS.

    Retorna `None` se gateway_id inexistente → VIEW responde 401 anti-oráculo.
    """
    from django.db import connection as _conn

    with _conn.cursor() as cur:
        cur.execute(
            "SELECT tenant_id, titulo_id FROM resolver_cr_titulo_por_gateway(%s)",
            [gateway_id],
        )
        row = cur.fetchone()
    if row is None:
        return None
    return UUID(str(row[0])), UUID(str(row[1]))


def _resposta_401() -> Response:
    """401 anti-oráculo: gateway_id inexistente ≡ HMAC inválido (D-CR-8 / R7)."""
    return Response(
        {"codigo": "nao_autorizado", "detalhe": "webhook nao autorizado."},
        status=status.HTTP_401_UNAUTHORIZED,
    )


def _obter_provider() -> PaymentGatewayProvider:
    """Instancia o MockPaymentGatewayProvider para o webhook (molde views.py)."""
    from django.conf import settings as _settings

    from src.domain.contas_receber.mock_provider import MockPaymentGatewayProvider, ModoMock

    modo_str = getattr(_settings, "CR_GATEWAY_PROVIDER_MOCK_MODO", "always_confirm")
    try:
        modo = ModoMock(modo_str)
    except ValueError:
        modo = ModoMock.ALWAYS_CONFIRM
    return MockPaymentGatewayProvider(modo=modo)


# authz-check: skip -- endpoint PUBLICO via PublicEndpoint mixin (HMAC = autorização, D-CR-8)
class ContasReceberWebhookView(PublicEndpoint, APIView):
    """POST webhook de baixa automática via gateway (T-CR-036 / D-CR-8).

    Anti-oráculo (R7): gateway_id inexistente E HMAC inválido → 401 IGUAIS.
    """

    authentication_classes: list[Any] = []
    permission_classes: list[Any] = []

    def post(self, request: Request) -> Response:
        ip_hash = _webhook_hash_ip(_webhook_extrair_ip(request))
        if not _webhook_rate_limit_ok(ip_hash):
            resp = Response(
                {"codigo": "rate_limit_excedido", "detalhe": "muitas requisicoes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            resp["Retry-After"] = str(_WEBHOOK_JANELA_SEG)
            return resp

        payload_bytes = request.body
        signature = request.META.get("HTTP_X_GATEWAY_SIGNATURE", "") or ""

        # Extrai titulo_gateway_id do payload para lookup (anti-oráculo: sem short-circuit).
        titulo_gateway_id_hint = ""
        try:
            decoded = payload_bytes.decode("utf-8")
            partes = decoded.split("|")
            if len(partes) >= 2:
                titulo_gateway_id_hint = partes[1]
        except Exception:
            logger.debug("cr webhook: payload nao e UTF-8 — HMAC vai rejeitar", exc_info=True)

        # Resolve tenant via SECURITY DEFINER ANTES do contexto de tenant.
        resultado_resolver = None
        if titulo_gateway_id_hint:
            resultado_resolver = _resolver_cr_titulo_por_gateway(titulo_gateway_id_hint)

        provider = _obter_provider()
        repo = DjangoTituloRepository()

        # Anti-oráculo: se gateway_id não encontrado, ainda tenta validar HMAC
        # para manter timing parecido (timing real = GATE-CR-ASAAS pentest).
        if resultado_resolver is None:
            try:
                provider.verificar_webhook(payload_bytes, signature)
            except Exception:
                logger.debug("cr webhook: anti-oraculo timing HMAC (gateway_id nao encontrado)")
            logger.warning(
                "cr webhook: gateway_id nao encontrado (anti-oraculo 401)",
                extra={"ip_hash": ip_hash, "hint": titulo_gateway_id_hint},
            )
            return _resposta_401()

        tenant_id, _titulo_id_resolvido = resultado_resolver

        try:
            with run_in_tenant_context(tenant_id), transaction.atomic():
                inp = processar_webhook_pagamento.ProcessarWebhookInput(
                    tenant_id=tenant_id,
                    payload_bytes=payload_bytes,
                    signature=signature,
                )
                out = processar_webhook_pagamento.processar_webhook_pagamento(
                    inp,
                    repo=repo,
                    provider=provider,
                )

                if not out.ja_processado:
                    assert out.pagamento is not None
                    from src.infrastructure.audit.event_helpers import publicar_evento as _pub

                    causation_uuid = UUID(int=0)

                    _pub(
                        acao="contas_receber.pago",
                        payload={
                            "titulo_id": str(out.pagamento.titulo_id),
                            "pagamento_id": str(out.pagamento.pagamento_id),
                            "valor_centavos": out.pagamento.valor.centavos,
                            "data": out.pagamento.data.isoformat(),
                            "origem": out.pagamento.origem.value,
                            "gateway_event_id": out.evento.gateway_event_id,
                            "novo_estado": out.novo_estado.value if out.novo_estado else None,
                        },
                        causation_id=causation_uuid,
                        tenant_id=tenant_id,
                        usuario_id=None,
                        resource_summary=(
                            f"titulo_receber {out.pagamento.titulo_id} pago via webhook"
                        ),
                    )
                    # Publica os.paga se titulo tem os_id_origem
                    titulo_pago = repo.obter_por_id(
                        tenant_id=tenant_id, titulo_id=out.pagamento.titulo_id
                    )
                    if titulo_pago is not None and titulo_pago.os_id_origem:
                        _pub(
                            acao="os.paga",
                            payload={"os_id": str(titulo_pago.os_id_origem)},
                            causation_id=causation_uuid,
                            tenant_id=tenant_id,
                            usuario_id=None,
                            resource_summary=(
                                f"os {titulo_pago.os_id_origem} paga via cr webhook"
                            ),
                        )

        except WebhookHMACInvalido:
            logger.warning(
                "cr webhook: HMAC invalido",
                extra={
                    "ip_hash": ip_hash,
                    "tenant_id": str(tenant_id),
                    "correlation_id": "webhook_hmac_invalido",
                },
            )
            # Publica incidente segurança (D-CR-8 / INV-FIN-GW-001)
            try:
                with run_in_tenant_context(tenant_id), transaction.atomic():
                    from src.infrastructure.audit.event_helpers import publicar_evento as _pub2

                    _pub2(
                        acao="contas_receber.webhook_hmac_rejeitado",
                        payload={
                            "ip_hash": ip_hash,
                            "titulo_gateway_id_hint": titulo_gateway_id_hint,
                        },
                        causation_id=UUID(int=0),
                        tenant_id=tenant_id,
                        usuario_id=None,
                        resource_summary="webhook_hmac_invalido contas_receber",
                    )
            except Exception:
                logger.warning("falha ao publicar incidente webhook_hmac_invalido", exc_info=True)
            return _resposta_401()

        return Response({"codigo": "ok"}, status=status.HTTP_200_OK)


contas_receber_webhook_view = ContasReceberWebhookView.as_view()
