"""ViewSet de vínculo cliente↔tabela de preço + helper de papel do decisor.

Extraído de views.py (refactor mecânico — sem mudança de comportamento).
Arquivo-fonte original: src/infrastructure/precificacao/views.py

Contém:
  - _derivar_papel_decisor  (helper usado por AprovacaoDescontoViewSet.decidir)
  - VinculoTabelaClienteViewSet (T-PRC-035e — AC-PRC-005-1 MÉDIO-2 P9)

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID, uuid4

from django.db import DataError, IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from src.domain.precificacao.enums import Alcada
from src.infrastructure.calibracao.lgpd import (
    derivar_hash_texto_canonicalizado,
    derivar_user_id_hash,
)
from src.infrastructure.idempotencia.services_idempotencia import concluir_chave
from src.infrastructure.multitenant.context import usuario_id_context
from src.infrastructure.precificacao._views_suporte import (
    _aplicar_idempotencia,
    _falha,
    _PrecificacaoViewSetBase,
    _publicar_evento_precificacao,
    _tenant_ou_none,
    _usuario_id_ou_none,
)
from src.infrastructure.precificacao.serializers import (
    CriarVinculoTabelaSerializer,
    RevogarVinculoSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: derivar papel do decisor a partir das permissões do usuário
# ---------------------------------------------------------------------------


def _derivar_papel_decisor(request: Request, tenant_id: UUID) -> Alcada:
    """Deriva a Alcada do decisor a partir das permissões do authz_perfil_acao.

    Predicate `alcada_cobre` (apps.py) verifica se o papel do usuário
    cobre a alçada exigida no pedido (T-PRC-036 / INV-PRC-APROVACAO-INDEPENDENTE).

    Hierarquia: DONO > GERENTE > LIVRE.

    Usa DjangoAuthorizationProvider — NÃO o `has_perm` Django nativo (que usa
    auth_permission/ContentType, não authz_perfil_acao).
    """
    usuario_id = usuario_id_context.get()
    if not request.user or usuario_id is None:
        return Alcada.LIVRE
    from src.infrastructure.authz.django_provider import get_provider

    provider = get_provider()
    if provider.can(
        usuario_id=usuario_id,
        action="precificacao.alcada_dono",
        resource={},
        tenant_id=tenant_id,
        purpose="alcada_decisor",
    ).allowed:
        return Alcada.DONO
    if provider.can(
        usuario_id=usuario_id,
        action="precificacao.alcada_gerente",
        resource={},
        tenant_id=tenant_id,
        purpose="alcada_decisor",
    ).allowed:
        return Alcada.GERENTE
    return Alcada.LIVRE


# ---------------------------------------------------------------------------
# T-PRC-035e: VinculoTabelaClienteViewSet (AC-PRC-005-1 — MÉDIO-2 P9)
# ---------------------------------------------------------------------------


class VinculoTabelaClienteViewSet(_PrecificacaoViewSetBase):
    """AC-PRC-005-1 — criar / revogar / listar vínculos cliente↔tabela de preço.

    Endpoint: /api/v1/precificacao/vinculos/
      POST   /criar/         → cria vínculo (Idempotency-Key obrigatório)
      POST   /{id}/revogar/  → revoga vínculo ativo
      GET    /               → lista vínculos ativos do tenant

    Autorização: `precificacao.configurar` (configurar tabela é configuração).
    Eventos D-PRC-9: cadeia hash central, outbox=False, PII=cliente_id_hash.
    """

    ACTION_MAP: ClassVar[dict[str, str]] = {
        "criar": "precificacao.configurar",
        "revogar": "precificacao.configurar",
        "list": "precificacao.ver",
    }

    @action(detail=False, methods=["post"], url_path="criar")
    def criar(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = CriarVinculoTabelaSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:vinculos:criar",
            payload_fingerprint={
                "cliente_id": str(dados["cliente_id"]),
                "tabela_id": str(dados["tabela_id"]),
            },
        )
        if resp_erro is not None:
            return resp_erro

        try:
            agora = datetime.now(UTC)
            vigencia_inicio = dados.get("vigencia_inicio") or agora
            vigencia_fim = dados.get("vigencia_fim")

            from src.domain.precificacao.entities import VinculoTabelaPrecoCliente
            from src.domain.shared.value_objects import JanelaVigencia

            vinculo = VinculoTabelaPrecoCliente(
                id=uuid4(),
                tenant_id=tenant_id,
                tabela_id=UUID(str(dados["tabela_id"])),
                cliente_id=UUID(str(dados["cliente_id"])),
                vigencia=JanelaVigencia(
                    inicio=vigencia_inicio,
                    fim=vigencia_fim,
                    revogado_em=None,
                    motivo_revogacao=None,
                ),
                criado_por=usuario_id,
            )

            with transaction.atomic():
                from src.infrastructure.precificacao.repositories import (
                    DjangoVinculoTabelaRepository,  # -- import local evita ciclo views→repositories
                )

                repo_vinculo = DjangoVinculoTabelaRepository()
                repo_vinculo.salvar(vinculo)

                _publicar_evento_precificacao(
                    acao="Precificacao.VinculoTabelaCriado",
                    payload={
                        "vinculo_id": str(vinculo.id),
                        "tabela_id": str(vinculo.tabela_id),
                        "cliente_id_hash": derivar_user_id_hash(
                            usuario_id=vinculo.cliente_id, tenant_id=tenant_id
                        ),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=vinculo.id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"vinculo:{vinculo.id}",
                )

        except (DataError, IntegrityError) as exc:
            return _falha(
                UUID(int=0), tenant_id, exc, status.HTTP_409_CONFLICT, chave_idempotencia=novo
            )

        corpo_resumo = {
            "vinculo_id": str(vinculo.id),
            "cliente_id": str(vinculo.cliente_id),
            "tabela_id": str(vinculo.tabela_id),
        }
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo=corpo_resumo,
            )
        return Response(corpo_resumo, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="revogar")
    def revogar(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        vinculo_id = self._uuid_ou_404(pk)

        ser = RevogarVinculoSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:vinculos:revogar",
            payload_fingerprint={"vinculo_id": str(vinculo_id)},
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                from src.infrastructure.precificacao.repositories import (
                    DjangoVinculoTabelaRepository,  # -- import local evita ciclo views→repositories
                )

                repo_vinculo = DjangoVinculoTabelaRepository()
                agora = datetime.now(UTC)
                repo_vinculo.revogar(
                    tenant_id=tenant_id,
                    vinculo_id=vinculo_id,
                    revogado_em=agora,
                    motivo=dados["motivo"],
                )
                _publicar_evento_precificacao(
                    acao="Precificacao.VinculoTabelaRevogado",
                    payload={
                        "vinculo_id": str(vinculo_id),
                        "motivo_hash": derivar_hash_texto_canonicalizado(
                            texto=dados["motivo"], tenant_id=tenant_id
                        ),
                        "revogado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=vinculo_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"vinculo:{vinculo_id}",
                )
        except RuntimeError as exc:
            return _falha(
                vinculo_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idempotencia=novo
            )

        corpo_resumo = {"vinculo_id": str(vinculo_id), "revogado": True}
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo=corpo_resumo,
            )
        return Response(corpo_resumo, status=status.HTTP_200_OK)

    def list(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        from src.infrastructure.precificacao.models import (
            VinculoTabelaPrecoCliente as VinculoModel,  # -- import local: model só neste path de listagem
        )

        qs = VinculoModel.objects.filter(
            tenant_id=tenant_id, revogado_em__isnull=True
        ).order_by("vigencia_inicio")
        resultado = [
            {
                "vinculo_id": str(v.id),
                "cliente_id": str(v.cliente_id),
                "tabela_id": str(v.tabela_id),
                "vigencia_inicio": v.vigencia_inicio.isoformat(),
                "vigencia_fim": v.vigencia_fim.isoformat() if v.vigencia_fim else None,
            }
            for v in qs
        ]
        return Response(resultado, status=status.HTTP_200_OK)
