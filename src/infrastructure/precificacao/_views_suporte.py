"""Helpers compartilhados dos ViewSets de precificacao.

Extraído de views.py (refactor mecânico — sem mudança de comportamento).
Contém helpers de contexto, idempotência, eventos e a base ViewSet.
Importado por views.py e _views_vinculo.py.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar
from uuid import UUID

from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    falhar_chave,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    correlation_id_context,
    usuario_id_context,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de contexto
# ---------------------------------------------------------------------------


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _usuario_id_ou_none() -> UUID | None:
    return usuario_id_context.get()


def _pode_ver_margem(request: Request) -> bool:
    """Verifica se o usuário tem permissão `precificacao.ver_margem` (D-PRC-4).

    Usa DjangoAuthorizationProvider (authz_perfil_acao) — NÃO o `has_perm` Django
    nativo que usa auth_permission/ContentType (esses modelos não são populados
    pelo seed de precificacao). Fail-closed: qualquer ausência de contexto → False.
    """
    usuario_id = usuario_id_context.get()
    tenant_id = active_tenant_context.get()
    if not request.user or usuario_id is None or tenant_id is None:
        return False
    from src.infrastructure.authz.django_provider import get_provider

    decision = get_provider().can(
        usuario_id=usuario_id,
        action="precificacao.ver_margem",
        resource={},
        tenant_id=tenant_id,
        purpose="rbac_campo_margem",
    )
    return decision.allowed


# ---------------------------------------------------------------------------
# Idempotência (molde PPS / configuracoes)
# ---------------------------------------------------------------------------


def _resposta_erro_idempotencia(erro: ErroValidacao) -> Response:
    body = {"codigo": erro.codigo, "detalhe": erro.detalhe}
    if erro.headers:
        return Response(body, status=erro.http_status, headers=erro.headers)
    return Response(body, status=erro.http_status)


def _aplicar_idempotencia(
    request: Request,
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    endpoint: str,
    payload_fingerprint: dict[str, Any],
) -> tuple[NovoProcessamento | None, Response | None]:
    avaliacao = avaliar_chave_idempotencia(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        endpoint=endpoint,
        chave_header=request.META.get("HTTP_IDEMPOTENCY_KEY"),
        payload=payload_fingerprint,
    )
    if isinstance(avaliacao, ErroValidacao):
        return None, _resposta_erro_idempotencia(avaliacao)
    if isinstance(avaliacao, Replay):
        return None, Response(
            avaliacao.response_body_resumo or {}, status=avaliacao.response_status
        )
    assert isinstance(avaliacao, NovoProcessamento)
    return avaliacao, None


# ---------------------------------------------------------------------------
# Eventos precificacao (cadeia hash — outbox=False, D-PRC-9)
# ---------------------------------------------------------------------------


def _publicar_evento_precificacao(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Evento `Precificacao.*` na cadeia hash central (outbox=False — D-PRC-9).

    Payload NUNCA inclui Parametros/Faixas em claro (INV-PRC-SEGREDO-LOG).
    Import local (molde fiscal/configuracoes).
    """
    from src.infrastructure.audit.event_helpers import (
        publicar_evento,  # -- import local evita ciclo infra→infra detectado em M8/M9
    )

    publicar_evento(
        acao=acao,
        payload=payload,
        causation_id=causation_id,
        tenant_id=tenant_id,
        usuario_id=usuario_id if usuario_id != UUID(int=0) else None,
        resource_summary=resource_summary,
        outbox=False,
    )
    logger.info(
        "precificacao evento WORM registrado na transacao",
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": str(causation_id),
        },
    )


# ---------------------------------------------------------------------------
# Helpers de erro sem custo/margem (INV-PRC-SEGREDO-LOG)
# ---------------------------------------------------------------------------


def _obter_correlation_id_views() -> str | None:
    """Lê correlation_id do ContextVar do request (MÉDIO-4 P9 — conserto 2ª passada).

    Fonte correta: `correlation_id_context` (ContextVar) setado pelo
    `CorrelationIdMiddleware` no início de cada request HTTP e devolvido
    no header `X-Correlation-ID`. É a mesma fonte que o ramo de sucesso
    (`_publicar_evento_precificacao`) usa via `correlation_id` do envelope.

    Anterior (FALSO): lia `current_setting('app.correlation_id')` via
    `event_helpers._obter_correlation_id` — esse GUC nunca é setado por
    `setar_contexto_pg_na_conexao`, portanto retornava sempre None no path real.
    """
    valor = correlation_id_context.get()
    return valor if valor else None


def _falha(
    chave_id: UUID,
    tenant_id: UUID,
    exc: Exception,
    http_status: int,
    chave_idempotencia: NovoProcessamento | None = None,
) -> Response:
    """Registra erro 4xx SEM custo/margem no log (INV-PRC-SEGREDO-LOG).

    MÉDIO-4 P9: inclui correlation_id no extra (paridade com ramo de sucesso
    em `_publicar_evento_precificacao`) para rastreabilidade forense end-to-end.
    """
    logger.warning(
        "precificacao acao recusada",
        extra={
            "chave_id": str(chave_id),
            "http_status": http_status,
            "erro": type(exc).__name__,
            # Não loga str(exc) — pode conter margem/custo (INV-PRC-SEGREDO-LOG)
            "tenant_id": str(tenant_id),
            "correlation_id": _obter_correlation_id_views(),
        },
    )
    if chave_idempotencia is not None and chave_idempotencia.chave_id is not None:
        try:
            falhar_chave(
                chave_id=chave_idempotencia.chave_id,
                tenant_id=tenant_id,
                response_status=http_status,
            )
        except Exception as _exc_idemp:  # -- falha no registro de idempotencia nunca mascara o erro original de negocio (design intencional)
            logger.warning(
                "precificacao falhar_chave ignorada (erro original prevalece)",
                extra={"tenant_id": str(tenant_id), "erro": type(_exc_idemp).__name__},
            )
    return Response(
        {"codigo": type(exc).__name__, "detalhe": type(exc).__name__}, status=http_status
    )


def _falha_404(msg: str) -> Response:
    from rest_framework import status as drf_status

    return Response(
        {"codigo": "NaoEncontrado", "detalhe": msg}, status=drf_status.HTTP_404_NOT_FOUND
    )


# ---------------------------------------------------------------------------
# Base ViewSet (molde _CatalogoViewSetBase PPS)
# ---------------------------------------------------------------------------


class _PrecificacaoViewSetBase(viewsets.ViewSet):
    """Base: ACTION_MAP authz + helpers comuns (molde PPS / configuracoes)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP: ClassVar[dict[str, str]] = {}

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    @staticmethod
    def _uuid_ou_404(raw: str | None) -> UUID:
        try:
            return UUID(str(raw))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id inválido: {exc}") from exc
