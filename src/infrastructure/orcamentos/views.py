"""ViewSet REST do modulo `orcamentos` (Fatia 2 / Onda 2a — T-ORC-037 parcial).

Actions desta onda:
  POST /api/v1/orcamentos/                 create      -> orcamento.criar
  GET  /api/v1/orcamentos/                 list        -> orcamento.ver
  GET  /api/v1/orcamentos/{id}/            retrieve    -> orcamento.ver
  POST /api/v1/orcamentos/{id}/itens/      adicionar_item -> orcamento.editar
  POST /api/v1/orcamentos/{id}/itens/{item_id}/editar/  editar_item -> orcamento.editar

Arquitetura use-case x view (D-FATIA2-C / TL-ORC ALTO-2): a VIEW (infra) monta as
deps de `calcular_precos` (resolver_preco_fn anti-N+1 + aliquota + repos), chama-o,
e passa o `ItemCalculado` resolvido ao use case (fino), que persiste SO o carimbo
probatorio (INV-ORC-MARGEM-OFF). Reusa `_construir_resolver_com_tabela_padrao`/
`_aliquota_imposto_fn` de `precificacao/views.py` (import local — sem ciclo).

PII do cliente derivada server-side (ADR-0032/0064 — molde calibracao/views.py).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar
from uuid import UUID

from django.db import DataError, IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.comercial.orcamentos import criar_orcamento as uc_criar
from src.application.comercial.orcamentos import itens as uc_itens
from src.domain.comercial.orcamentos.enums import TipoAtividadeAlvo
from src.domain.comercial.orcamentos.erros import ErroOrcamento, TabelaPrecoExpirada
from src.domain.comercial.orcamentos.value_objects import CondicoesPagamento
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.domain.precificacao.erros import ParametrosInviaveis, PrecoMinimoViolado
from src.domain.produtos_pecas_servicos.erros import CatalogoError
from src.domain.shared.value_objects import JanelaVigencia
from src.infrastructure.idempotencia.services_idempotencia import concluir_chave
from src.infrastructure.orcamentos._views_suporte import (
    _aplicar_idempotencia,
    _falha_404,
    _falha_erro_orcamento,
    _OrcamentoViewSetBase,
    _pode_ver_margem,
    _tenant_ou_none,
    _usuario_id_ou_none,
)
from src.infrastructure.orcamentos.repositories import DjangoOrcamentoRepository
from src.infrastructure.orcamentos.serializers import (
    AdicionarItemSerializer,
    CriarOrcamentoSerializer,
    EditarItemSerializer,
    serializar_item,
    serializar_orcamento,
)

if TYPE_CHECKING:
    from src.domain.comercial.orcamentos.entities import Orcamento
    from src.domain.configuracoes_sistema.repository import SerieDocumentoRepository
    from src.domain.precificacao.value_objects import ItemCalculado

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Seams cross-modulo (import local — molde do projeto, evita ciclo infra->infra)
# ---------------------------------------------------------------------------


def _verificar_cliente(cliente_id: UUID, tenant_id: UUID) -> uc_criar.StatusCliente:
    """Le o model `Cliente` (cross-modulo, sob RLS) + property `bloqueado` (D-ORC-4)."""
    from src.infrastructure.clientes.models import Cliente

    obj = Cliente.objects.filter(id=cliente_id, tenant_id=tenant_id).first()
    if obj is None:
        return uc_criar.StatusCliente(existe=False, ativo=False, bloqueado=False)
    return uc_criar.StatusCliente(
        existe=True,
        ativo=obj.deletado_em is None,
        bloqueado=obj.bloqueado,
    )


def _resolver_tabela_efetiva(
    *,
    tenant_id: UUID,
    orcamento: Orcamento,
    tabela_id_payload: UUID | None,
    agora: datetime,
) -> UUID | None:
    """Tabela de preco efetiva: payload > tabela do orcamento > vinculo do cliente.

    None => fallback para tabela padrao do tenant em `preco_para_os` (D-PRC-12).
    """
    if tabela_id_payload is not None:
        return tabela_id_payload
    if orcamento.tabela_preco_id is not None:
        return orcamento.tabela_preco_id
    if orcamento.cliente_atual_id is not None:
        from src.infrastructure.precificacao.repositories import DjangoVinculoTabelaRepository

        vinculo = DjangoVinculoTabelaRepository().obter_por_cliente(
            tenant_id=tenant_id, cliente_id=orcamento.cliente_atual_id, em=agora
        )
        if vinculo is not None:
            return vinculo.tabela_id
    return None


def _calcular_item_unico(
    *,
    tenant_id: UUID,
    catalogo_item_id: UUID,
    desconto_pct: Decimal,
    km: Decimal,
    parcelas: int,
    tabela_id: UUID | None,
    cliente_id: UUID | None,
    agora: datetime,
) -> tuple[ItemCalculado, Decimal, Decimal]:
    """Calcula o preco de UM item (cesta de 1) reusando o motor de precificacao.

    Retorna (ItemCalculado, aliquota_imposto_fracao, comissao_fracao). As deps
    (resolver anti-N+1 + aliquota) vem de `precificacao/views.py` (D-FATIA2-C).
    """
    from src.application.precificacao import calculo as uc_calculo
    from src.domain.precificacao.enums import ModoMontagem
    from src.domain.precificacao.portas import CustoProviderStub
    from src.infrastructure.precificacao.repositories import (
        DjangoFaixaRepository,
        DjangoParametrosRepository,
        DjangoRegraRepository,
    )
    from src.infrastructure.precificacao.views import (
        _aliquota_imposto_fn,
        _construir_resolver_com_tabela_padrao,
    )

    resolver_preco_fn = _construir_resolver_com_tabela_padrao(tenant_id, agora)
    repo_params = DjangoParametrosRepository()

    resultado = uc_calculo.calcular_precos(
        uc_calculo.CalcularPrecosInput(
            tenant_id=tenant_id,
            itens=(uc_calculo.ItemCestaInput(item_id=catalogo_item_id, tabela_id=tabela_id),),
            desconto_pct=desconto_pct,
            modo_montagem=ModoMontagem.FECHADO_COM_AVISO,
            km=km,
            parcelas=parcelas,
            agora=agora,
            cliente_id=cliente_id,
        ),
        repo_regra=DjangoRegraRepository(),
        repo_faixa=DjangoFaixaRepository(),
        repo_params=repo_params,
        custo_provider=CustoProviderStub(),
        resolver_preco_fn=resolver_preco_fn,
        aliquota_imposto_fn=_aliquota_imposto_fn,
    )
    item_calc = resultado.itens[0]
    aliquota_fracao = Decimal(resultado.eco_entradas["aliquota_imposto_fracao"])
    params = repo_params.obter_vigentes(tenant_id=tenant_id)
    comissao_fracao = params.pct_comissao_prevista.fracao() if params is not None else Decimal("0")
    return item_calc, aliquota_fracao, comissao_fracao


# ---------------------------------------------------------------------------
# OrcamentoViewSet
# ---------------------------------------------------------------------------


class OrcamentoViewSet(_OrcamentoViewSetBase):
    """US-ORC-001/004 — criar orcamento + gerir itens (Onda 2a)."""

    ACTION_MAP: ClassVar[dict[str, str]] = {
        "create": "orcamento.criar",
        "list": "orcamento.ver",
        "retrieve": "orcamento.ver",
        "adicionar_item": "orcamento.editar",
        "editar_item": "orcamento.editar",
    }

    # ----- criar (POST /orcamentos/) --------------------------------

    def create(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = CriarOrcamentoSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data
        cliente_id = UUID(str(dados["cliente_id"]))

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="orcamentos:criar",
            payload_fingerprint={
                "cliente_id": str(cliente_id),
                "validade_dias": dados["validade_dias"],
                "criado_por": str(usuario_id),
            },
        )
        if resp_erro is not None:
            return resp_erro

        from src.infrastructure.calibracao.lgpd import (
            derivar_cliente_key_id,
            derivar_cliente_referencia_hash,
        )

        agora = datetime.now(UTC)
        validade = JanelaVigencia(
            inicio=agora, fim=agora + timedelta(days=int(dados["validade_dias"]))
        )
        cond = dados.get("condicoes_pagamento") or {}
        condicoes = CondicoesPagamento(
            parcelas=int(cond.get("parcelas", 1)),
            forma_pagamento=str(cond.get("forma_pagamento", "pix")),
            dias_vencimento_primeira=int(cond.get("dias_vencimento_primeira", 0)),
            intervalo_dias=int(cond.get("intervalo_dias", 30)),
            observacoes=cond.get("observacoes"),
        )

        try:
            with transaction.atomic():
                out = uc_criar.criar_orcamento(
                    uc_criar.CriarOrcamentoInput(
                        tenant_id=tenant_id,
                        criado_por=usuario_id,
                        cliente_id=cliente_id,
                        cliente_referencia_hash=derivar_cliente_referencia_hash(
                            cliente_id=cliente_id, tenant_id=tenant_id
                        ),
                        cliente_key_id=derivar_cliente_key_id(tenant_id=tenant_id),
                        condicoes_pagamento=condicoes,
                        validade=validade,
                        agora=agora,
                        template_id=dados.get("template_id"),
                        tabela_preco_id=dados.get("tabela_preco_id"),
                        observacoes=dados.get("observacoes"),
                        responsavel_id=dados.get("responsavel_id"),
                        chamado_origem_id=dados.get("chamado_origem_id"),
                    ),
                    repo=DjangoOrcamentoRepository(),
                    repo_serie=_serie_repo(),
                    verificar_cliente_fn=_verificar_cliente,
                )
        except ErroOrcamento as exc:
            return _falha_erro_orcamento(exc, tenant_id=tenant_id, chave_idempotencia=novo)
        except (DataError, IntegrityError):
            # _falha_erro_orcamento ja loga com tenant_id + correlation_id (OBS-002).
            return _falha_erro_orcamento(
                _conflito("conflito ao criar orcamento"),
                tenant_id=tenant_id,
                chave_idempotencia=novo,
            )

        corpo = serializar_orcamento(out.orcamento, pode_ver_margem=_pode_ver_margem(request))
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo={"id": str(out.orcamento.id), "numero": out.orcamento.numero},
            )
        return Response(corpo, status=status.HTTP_201_CREATED)

    # ----- leitura --------------------------------------------------

    def list(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        repo = DjangoOrcamentoRepository()
        orcamentos = repo.listar(tenant_id=tenant_id)
        pode_ver = _pode_ver_margem(request)
        return Response(
            [serializar_orcamento(o, pode_ver_margem=pode_ver) for o in orcamentos],
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        orcamento_id = self._uuid_ou_404(pk)
        repo = DjangoOrcamentoRepository()
        orcamento = repo.get_by_id(orcamento_id, tenant_id=tenant_id)
        if orcamento is None:
            return _falha_404(f"orcamento {orcamento_id} nao encontrado")
        versao = repo.get_versao_ativa(orcamento_id, tenant_id=tenant_id)
        itens = (
            repo.listar_itens_versao(versao.id, tenant_id=tenant_id) if versao is not None else []
        )
        return Response(
            serializar_orcamento(orcamento, pode_ver_margem=_pode_ver_margem(request), itens=itens),
            status=status.HTTP_200_OK,
        )

    # ----- adicionar item (POST /orcamentos/{id}/itens/) ------------

    @action(detail=True, methods=["post"], url_path="itens")
    def adicionar_item(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        orcamento_id = self._uuid_ou_404(pk)

        ser = AdicionarItemSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        repo = DjangoOrcamentoRepository()
        orcamento = repo.get_by_id(orcamento_id, tenant_id=tenant_id)
        if orcamento is None:
            return _falha_404(f"orcamento {orcamento_id} nao encontrado")

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="orcamentos:adicionar_item",
            payload_fingerprint={
                "orcamento_id": str(orcamento_id),
                "catalogo_item_id": str(dados["catalogo_item_id"]),
                "quantidade": str(dados["quantidade"]),
                "desconto_pct": str(dados["desconto_pct"]),
            },
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                resultado = self._processar_item(
                    repo=repo,
                    tenant_id=tenant_id,
                    orcamento=orcamento,
                    dados=dados,
                    item_id=None,
                )
        except TabelaPrecoExpirada as exc:
            return _falha_erro_orcamento(exc, tenant_id=tenant_id, chave_idempotencia=novo)
        except CatalogoError as exc:
            # preco/linha ausente ou sem vigencia na data (D-ORC: tabela expirada) -> 422
            return _falha_erro_orcamento(
                TabelaPrecoExpirada(f"preco indisponivel para o item: {type(exc).__name__}"),
                tenant_id=tenant_id,
                chave_idempotencia=novo,
            )
        except ErroOrcamento as exc:
            return _falha_erro_orcamento(exc, tenant_id=tenant_id, chave_idempotencia=novo)
        except (ParametrosInviaveis, PrecoMinimoViolado) as exc:
            return _falha_erro_orcamento(
                _unprocessable(type(exc).__name__),
                tenant_id=tenant_id,
                chave_idempotencia=novo,
            )

        corpo = {
            "item": serializar_item(resultado.item),
            "orcamento": serializar_orcamento(
                resultado.orcamento, pode_ver_margem=_pode_ver_margem(request)
            ),
        }
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo={
                    "item_id": str(resultado.item.id),
                    "orcamento_id": str(resultado.orcamento.id),
                },
            )
        return Response(corpo, status=status.HTTP_201_CREATED)

    # ----- editar item (POST /orcamentos/{id}/itens/{item_id}/editar/) -----

    @action(
        detail=True,
        methods=["post"],
        url_path=r"itens/(?P<item_id>[0-9a-fA-F-]+)/editar",
    )
    def editar_item(
        self, request: Request, pk: str | None = None, item_id: str | None = None
    ) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        orcamento_id = self._uuid_ou_404(pk)
        item_uuid = self._uuid_ou_404(item_id)

        ser = EditarItemSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        repo = DjangoOrcamentoRepository()
        orcamento = repo.get_by_id(orcamento_id, tenant_id=tenant_id)
        if orcamento is None:
            return _falha_404(f"orcamento {orcamento_id} nao encontrado")

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="orcamentos:editar_item",
            payload_fingerprint={
                "orcamento_id": str(orcamento_id),
                "item_id": str(item_uuid),
                "catalogo_item_id": str(dados["catalogo_item_id"]),
                "quantidade": str(dados["quantidade"]),
                "desconto_pct": str(dados["desconto_pct"]),
            },
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                resultado = self._processar_item(
                    repo=repo,
                    tenant_id=tenant_id,
                    orcamento=orcamento,
                    dados=dados,
                    item_id=item_uuid,
                )
        except TabelaPrecoExpirada as exc:
            return _falha_erro_orcamento(exc, tenant_id=tenant_id, chave_idempotencia=novo)
        except CatalogoError as exc:
            return _falha_erro_orcamento(
                TabelaPrecoExpirada(f"preco indisponivel para o item: {type(exc).__name__}"),
                tenant_id=tenant_id,
                chave_idempotencia=novo,
            )
        except ErroOrcamento as exc:
            return _falha_erro_orcamento(exc, tenant_id=tenant_id, chave_idempotencia=novo)
        except (ParametrosInviaveis, PrecoMinimoViolado) as exc:
            return _falha_erro_orcamento(
                _unprocessable(type(exc).__name__),
                tenant_id=tenant_id,
                chave_idempotencia=novo,
            )

        corpo = {
            "item": serializar_item(resultado.item),
            "orcamento": serializar_orcamento(
                resultado.orcamento, pode_ver_margem=_pode_ver_margem(request)
            ),
        }
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo={
                    "item_id": str(resultado.item.id),
                    "orcamento_id": str(resultado.orcamento.id),
                },
            )
        return Response(corpo, status=status.HTTP_200_OK)

    # ----- helper interno de calculo+persistencia de item -----------

    def _processar_item(
        self,
        *,
        repo: DjangoOrcamentoRepository,
        tenant_id: UUID,
        orcamento: Orcamento,
        dados: dict[str, Any],
        item_id: UUID | None,
    ) -> uc_itens.ItemOrcamentoOutput:
        """Calcula o preco (cesta de 1) e chama adicionar/editar item (D-FATIA2-C)."""
        agora = datetime.now(UTC)
        tabela_id = _resolver_tabela_efetiva(
            tenant_id=tenant_id,
            orcamento=orcamento,
            tabela_id_payload=dados.get("tabela_id"),
            agora=agora,
        )
        item_calc, aliquota_fracao, comissao_fracao = _calcular_item_unico(
            tenant_id=tenant_id,
            catalogo_item_id=UUID(str(dados["catalogo_item_id"])),
            desconto_pct=dados["desconto_pct"],
            km=dados["km"],
            parcelas=int(dados["parcelas"]),
            tabela_id=tabela_id,
            cliente_id=orcamento.cliente_atual_id,
            agora=agora,
        )
        equipamento_id = dados.get("equipamento_id")
        tipo_atividade = (
            TipoAtividadeAlvo(dados["tipo_atividade_alvo"])
            if dados.get("tipo_atividade_alvo")
            else None
        )
        tipo_comercial = (
            TipoItemComercial(dados["tipo_item_comercial"])
            if dados.get("tipo_item_comercial")
            else None
        )

        if item_id is None:
            return uc_itens.adicionar_item(
                uc_itens.AdicionarItemInput(
                    tenant_id=tenant_id,
                    orcamento_id=orcamento.id,
                    item_calculado=item_calc,
                    quantidade=dados["quantidade"],
                    descricao_snapshot=dados["descricao"],
                    aliquota_imposto_fracao=aliquota_fracao,
                    comissao_fracao=comissao_fracao,
                    equipamento_id=equipamento_id,
                    tipo_atividade_alvo=tipo_atividade,
                    tipo_item_comercial=tipo_comercial,
                ),
                repo=repo,
            )
        return uc_itens.editar_item(
            uc_itens.EditarItemInput(
                tenant_id=tenant_id,
                orcamento_id=orcamento.id,
                item_id=item_id,
                item_calculado=item_calc,
                quantidade=dados["quantidade"],
                descricao_snapshot=dados["descricao"],
                aliquota_imposto_fracao=aliquota_fracao,
                comissao_fracao=comissao_fracao,
                equipamento_id=equipamento_id,
                tipo_atividade_alvo=tipo_atividade,
                tipo_item_comercial=tipo_comercial,
            ),
            repo=repo,
        )


# ---------------------------------------------------------------------------
# Helpers de modulo
# ---------------------------------------------------------------------------


def _serie_repo() -> SerieDocumentoRepository:
    from src.infrastructure.configuracoes_sistema.repositories import (
        DjangoSerieDocumentoRepository,
    )

    return DjangoSerieDocumentoRepository()


def _conflito(msg: str) -> ErroOrcamento:
    exc = ErroOrcamento(msg)
    exc.codigo = "conflito_persistencia"
    exc.http_status = status.HTTP_409_CONFLICT
    return exc


def _unprocessable(nome: str) -> ErroOrcamento:
    exc = ErroOrcamento(nome)
    exc.codigo = nome
    exc.http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
    return exc
