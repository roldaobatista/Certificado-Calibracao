"""Helpers compartilhados dos ViewSets de `orcamentos` (molde precificacao).

Contexto (tenant/usuario), idempotencia (2 camadas), RBAC de margem
(`orcamento.ver_margem`), respostas de erro e a base ViewSet (ACTION_MAP authz).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar
from uuid import UUID

from rest_framework import status as drf_status
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.domain.comercial.orcamentos.erros import ErroOrcamento
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
# Contexto
# ---------------------------------------------------------------------------


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _usuario_id_ou_none() -> UUID | None:
    return usuario_id_context.get()


def _pode_ver_margem(request: Request) -> bool:
    """`orcamento.ver_margem` (D-ORC-10 / INV-ORC-MARGEM-OFF) — fail-closed.

    Usa DjangoAuthorizationProvider (authz_perfil_acao), NAO o `has_perm` Django
    nativo (auth_permission/ContentType nao sao populados pelos seeds do projeto).
    """
    usuario_id = usuario_id_context.get()
    tenant_id = active_tenant_context.get()
    if not getattr(request, "user", None) or usuario_id is None or tenant_id is None:
        return False
    from src.infrastructure.authz.django_provider import get_provider

    decision = get_provider().can(
        usuario_id=usuario_id,
        action="orcamento.ver_margem",
        resource={},
        tenant_id=tenant_id,
        purpose="rbac_campo_margem",
    )
    return decision.allowed


# ---------------------------------------------------------------------------
# Idempotencia (molde precificacao/_views_suporte)
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
# Respostas de erro
# ---------------------------------------------------------------------------


def _obter_correlation_id() -> str | None:
    valor = correlation_id_context.get()
    return valor if valor else None


def _falha_erro_orcamento(
    exc: ErroOrcamento,
    *,
    tenant_id: UUID,
    chave_idempotencia: NovoProcessamento | None = None,
) -> Response:
    """Traduz um `ErroOrcamento` para Response usando seu http_status canonico."""
    logger.warning(
        "orcamento acao recusada",
        extra={
            "codigo": exc.codigo,
            "http_status": exc.http_status,
            "tenant_id": str(tenant_id),
            "correlation_id": _obter_correlation_id(),
        },
    )
    if chave_idempotencia is not None and chave_idempotencia.chave_id is not None:
        try:
            falhar_chave(
                chave_id=chave_idempotencia.chave_id,
                tenant_id=tenant_id,
                response_status=exc.http_status,
            )
        except (
            Exception
        ) as _exc_idemp:  # -- registro de idempotencia nunca mascara o erro de negocio
            logger.warning(
                "orcamento falhar_chave ignorada (erro original prevalece)",
                extra={"tenant_id": str(tenant_id), "erro": type(_exc_idemp).__name__},
            )
    return Response({"codigo": exc.codigo, "detalhe": exc.mensagem}, status=exc.http_status)


def _falha_404(msg: str) -> Response:
    return Response(
        {"codigo": "NaoEncontrado", "detalhe": msg}, status=drf_status.HTTP_404_NOT_FOUND
    )


# ---------------------------------------------------------------------------
# Base ViewSet
# ---------------------------------------------------------------------------


class _OrcamentoViewSetBase(viewsets.ViewSet):
    """Base: ACTION_MAP authz + helpers comuns (molde precificacao)."""

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
            raise NotFound(f"id invalido: {exc}") from exc
