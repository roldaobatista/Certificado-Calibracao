"""ViewSets REST da frente `precificacao` (Fatia 2 — T-PRC-035).

Actions:
  POST /api/v1/precificacao/regras/publicar/              US-PRC-001
  POST /api/v1/precificacao/regras/{id}/revogar/          US-PRC-001
  GET  /api/v1/precificacao/regras/{id}/                  leitura
  GET  /api/v1/precificacao/regras/vigente/?item_id=      vigente por item
  POST /api/v1/precificacao/calcular/                     US-PRC-002 (SEM Idempotency-Key)
  POST /api/v1/precificacao/aprovacoes/solicitar/         US-PRC-003
  POST /api/v1/precificacao/aprovacoes/{id}/decidir/      US-PRC-004
  GET  /api/v1/precificacao/aprovacoes/pendentes/         leitura
  POST /api/v1/precificacao/config/faixas/                configurar_faixas
  POST /api/v1/precificacao/config/perfil/                configurar_perfil_composicao
  POST /api/v1/precificacao/config/parametros/            configurar_parametros

Autorização: RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP semântico.
Idempotency-Key: publicar / revogar / solicitar / decidir / faixas / perfil / parametros.
calcular NÃO usa Idempotency-Key (stateless — D-PRC-9).

RBAC de campo (D-PRC-4 / INV-PRC-MARGEM-RBAC):
  `filtrar_visao_margem` aplicado em TODOS serializers de saída desta frente.
  `pode_ver_margem = request.user.has_perm("precificacao.ver_margem")`.

Segredo comercial (INV-PRC-SEGREDO-LOG):
  custo / margem / parâmetros NUNCA em logs, exceptions, event payload.

Eventos `Precificacao.*` (ACOES_PRECIFICACAO) vão SÓ na cadeia hash central
(cadeia=True, outbox=False — D-PRC-9). Payload NUNCA inclui Parametros/Faixas
em claro. Hash via HMAC-tenant ADR-0029.

VinculoTabelaClienteViewSet e _derivar_papel_decisor vivem em _views_vinculo.py
(refactor mecânico — sem mudança de comportamento).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar
from uuid import UUID

if TYPE_CHECKING:
    from src.domain.produtos_pecas_servicos.entities import PrecoResolvido

from django.db import DataError, IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.precificacao import aprovacao as uc_aprovacao
from src.application.precificacao import calculo as uc_calculo
from src.application.precificacao import configuracao as uc_configuracao
from src.application.precificacao import regra as uc_regra
from src.domain.precificacao.enums import Alcada, ContextoTipo, EstadoPedido, ModoMontagem
from src.domain.precificacao.erros import (
    AlcadaInsuficiente,
    CustoRealIndisponivel,
    DecisorNaoIndependente,
    FaixasDescontoInvalidas,
    FingerprintDivergente,
    ParametrosInviaveis,
    PrecoMinimoViolado,
)
from src.infrastructure.calibracao.lgpd import (
    derivar_hash_texto_canonicalizado,
    derivar_user_id_hash,
)
from src.infrastructure.idempotencia.services_idempotencia import (
    concluir_chave,
    falhar_chave,
)

# Helpers compartilhados (extraídos em _views_suporte.py — refactor mecânico)
from src.infrastructure.precificacao._views_suporte import (
    _aplicar_idempotencia,
    _falha,
    _falha_404,
    _pode_ver_margem,
    _PrecificacaoViewSetBase,
    _publicar_evento_precificacao,
    _tenant_ou_none,
    _usuario_id_ou_none,
)

# _derivar_papel_decisor vive em _views_vinculo (extraído junto com VinculoTabelaClienteViewSet)
from src.infrastructure.precificacao._views_vinculo import _derivar_papel_decisor
from src.infrastructure.precificacao.repositories import (
    DjangoFaixaRepository,
    DjangoParametrosRepository,
    DjangoPedidoRepository,
    DjangoRegraRepository,
)
from src.infrastructure.precificacao.serializers import (
    CalcularPrecosSerializer,
    ConfigurarFaixasSerializer,
    ConfigurarParametrosSerializer,
    ConfigurarPerfilComposicaoSerializer,
    DecidirAprovacaoSerializer,
    PublicarRegraSerializer,
    RevogarRegraSerializer,
    SolicitarAprovacaoSerializer,
    serializar_faixa,
    serializar_parametros,
    serializar_pedido,
    serializar_regra,
    serializar_resultado_calculo,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de resolução de preço com fallback (D-PRC-12)
# ---------------------------------------------------------------------------


def _resolver_preco_com_fallback(
    tenant_id: UUID,
    item_id: UUID,
    tabela_id: UUID | None,
    data_ref: datetime,
    *,
    tabela_padrao_pre_resolvida: Any | None = None,
) -> PrecoResolvido:
    """Resolve preço via `preco_para_os` com fallback por item (D-PRC-12).

    D-PRC-12: se `tabela_id` não veio no ItemCestaInput, tenta resolver o
    vínculo `cliente_id → tabela_id` via VinculoTabelaPrecoCliente vigente
    na data_ref (ver chamador em `calcular`). Tabela específica → usa ela;
    sem linha na específica OU sem vínculo → tabela padrão (fallback por item
    — não viola ADR-0081: ambas são tabelas VENDA, nunca VENDA→lista).

    Anti-N+1 (TL-PRC-14 / PERF-MÉDIO-3 P9): `tabela_padrao_pre_resolvida`
    deve ser passada pelo chamador de cesta (resolvida UMA vez antes do loop).
    Quando None, delega ao `preco_para_os` que faz o `obter_padrao` — compatível
    com chamadas isoladas fora de cesta (PPS 100% preservado).
    """
    from src.infrastructure.produtos_pecas_servicos import (
        query_service,  # -- import local evita ciclo infra→infra; padrão consolidado no projeto (molde PPS views)
    )
    from src.infrastructure.produtos_pecas_servicos.repositories import (  # -- idem acima
        DjangoItemCatalogoRepository,
        DjangoTabelaPrecoRepository,
    )

    item_repo = DjangoItemCatalogoRepository()
    tabela_repo = DjangoTabelaPrecoRepository()

    return query_service.preco_para_os(
        tenant_id=tenant_id,
        item_id=item_id,
        data_referencia=data_ref,
        tabela_id=tabela_id,  # None → fallback padrão (D-PRC-12)
        item_repo=item_repo,
        tabela_repo=tabela_repo,
        tabela_padrao=tabela_padrao_pre_resolvida,  # anti-N+1: None faz obter_padrao no serviço
    )


def _construir_resolver_com_tabela_padrao(
    tenant_id: UUID,
    data_ref: datetime,
) -> uc_calculo.ResolverPrecoFn:
    """Cria closure de `ResolverPrecoFn` com tabela padrão resolvida UMA vez.

    Anti-N+1 (TL-PRC-14 / PERF-MÉDIO-3 P9): resolve `obter_padrao` ANTES
    de entrar no loop de itens do `calcular_precos`. A tabela padrão é
    constante por (tenant, request) — não precisa ser re-consultada por item.

    Se o tenant não tem tabela padrão (None), passa None → o `preco_para_os`
    vai levantar `PrecoTabelaAusenteError` no primeiro item sem linha específica
    (comportamento fail-closed preservado — D-PPS-2).
    """
    from src.infrastructure.produtos_pecas_servicos.repositories import (  # -- import local evita ciclo infra→infra
        DjangoTabelaPrecoRepository,
    )

    tabela_repo = DjangoTabelaPrecoRepository()
    tabela_padrao = tabela_repo.obter_padrao(tenant_id=tenant_id)  # 1 query por request

    def _resolver(
        t_id: UUID,
        item_id: UUID,
        tabela_id: UUID | None,
        data_ref_inner: datetime,
    ) -> PrecoResolvido:
        return _resolver_preco_com_fallback(
            t_id,
            item_id,
            tabela_id,
            data_ref_inner,
            tabela_padrao_pre_resolvida=tabela_padrao,
        )

    return _resolver


def _aliquota_imposto_fn(
    tenant_id: UUID,
    data_ref: datetime,
) -> tuple[Decimal, tuple[UUID, int] | None]:
    """Retorna alíquota de imposto vigente da frente configuracoes-sistema.

    D-PRC-10 — SIMULAÇÃO: alíquota vigente do tenant. "Cálculo fiscal exato"
    é non-goal do PRD.
    """
    try:
        from src.infrastructure.configuracoes_sistema.repositories import (  # -- import local evita ciclo infra→infra; imposto é modulo Wave A independente
            DjangoImpostoRepository,
        )

        imposto_repo = DjangoImpostoRepository()
        # D-PRC-10 simulação: usa o 1º imposto vigente encontrado (sem tipo específico)
        impostos = imposto_repo.listar(tenant_id=tenant_id)
        imposto = next(
            (
                i
                for i in impostos
                if i.vigencia.inicio <= data_ref
                and (i.vigencia.fim is None or i.vigencia.fim > data_ref)
                and i.vigencia.revogado_em is None
            ),
            None,
        )
        if imposto is not None:
            fracao = imposto.aliquota.valor / Decimal("100")
            return fracao, (imposto.id, 1)  # versao_n=1 (D-PRC-10 simulacao)
    except Exception as _exc_imp:  # -- imposto ausente nao bloqueia calculo (D-PRC-10 simulacao; fallback zero-taxa intencional, nao e mascaramento)
        logger.debug(
            "precificacao imposto ausente — fallback zero-taxa (D-PRC-10 simulacao)",
            extra={"tenant_id": str(tenant_id), "erro": type(_exc_imp).__name__},
        )
    return Decimal("0"), None


# ---------------------------------------------------------------------------
# Helper: hash de justificativa injetável em decidir_aprovacao
# ---------------------------------------------------------------------------


def _hash_justificativa(texto: str, tenant_id: UUID) -> str:
    """ADR-0029 + HMAC-tenant: hash canônico do texto da justificativa."""
    return derivar_hash_texto_canonicalizado(texto=texto, tenant_id=tenant_id)


def _salvar_justificativa(pedido_id: UUID, tenant_id: UUID, texto: str) -> None:
    """Persiste texto cru em JustificativaDecisaoDesconto (tabela-par D-PRC-15)."""
    from src.infrastructure.precificacao.models import (
        JustificativaDecisaoDesconto,  # -- import local evita ciclo models→views em precificacao; padrao para evitar referencia circular em apps grandes
    )

    JustificativaDecisaoDesconto.objects.create(
        pedido_id=pedido_id,
        tenant_id=tenant_id,
        texto=texto,
    )


# ---------------------------------------------------------------------------
# T-PRC-035a: RegraFormacaoPrecoViewSet
# ---------------------------------------------------------------------------


class RegraFormacaoPrecoViewSet(_PrecificacaoViewSetBase):
    """US-PRC-001 — publicar / revogar regra de formação de preço."""

    ACTION_MAP: ClassVar[dict[str, str]] = {
        "publicar": "precificacao.configurar",
        "revogar": "precificacao.configurar",
        "retrieve": "precificacao.ver",
        "vigente": "precificacao.ver",
    }

    @action(detail=False, methods=["post"], url_path="publicar")
    def publicar(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"detalhe": "contexto de tenant/usuário ausente"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ser = PublicarRegraSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:regras:publicar",
            payload_fingerprint={
                "item_id": str(dados["item_id"]),
                "modo": dados["modo"],
                "vigencia_inicio": str(dados.get("vigencia_inicio")),
            },
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                repo_regra = DjangoRegraRepository()
                from src.domain.precificacao.portas import (
                    CustoProviderStub,  # -- import local evita ciclo domain.portas importado apenas em paths de execucao (stub Wave A)
                )

                inp = uc_regra.PublicarRegraInput(
                    tenant_id=tenant_id,
                    item_id=UUID(str(dados["item_id"])),
                    modo=dados["modo"],
                    criado_por=usuario_id,
                    agora=datetime.now(UTC),
                    vigencia_inicio=dados.get("vigencia_inicio"),
                    preco_fixo=dados.get("preco_fixo"),
                    custo_manual_declarado=dados.get("custo_manual_declarado"),
                    custo_referencia_em=dados.get("custo_referencia_em"),
                    margem_alvo_pct=dados.get("margem_alvo_pct"),
                    margem_piso_pct=dados.get("margem_piso_pct"),
                )
                out = uc_regra.publicar_regra(
                    inp,
                    repo=repo_regra,
                    custo_provider=CustoProviderStub(),
                )
                pode_ver = _pode_ver_margem(request)
                regra_ser = serializar_regra(out.regra, pode_ver_margem=pode_ver)

                _publicar_evento_precificacao(
                    acao="Precificacao.RegraPublicada",
                    payload={
                        "regra_id": str(out.regra.id),
                        "item_id": str(out.regra.item_id),
                        "modo": out.regra.modo.value,
                        "versao_n": out.regra.versao_n,
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        # custo/margem NUNCA em claro (INV-PRC-SEGREDO-LOG)
                    },
                    causation_id=out.regra.id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"regra:{out.regra.id}",
                )

        except CustoRealIndisponivel as exc:
            return _falha(
                UUID(int=0),
                tenant_id,
                exc,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                chave_idempotencia=novo,
            )
        except ValueError as exc:
            return _falha(
                UUID(int=0),
                tenant_id,
                exc,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                chave_idempotencia=novo,
            )
        except (DataError, IntegrityError) as exc:
            return _falha(
                UUID(int=0), tenant_id, exc, status.HTTP_409_CONFLICT, chave_idempotencia=novo
            )

        corpo_resumo = {"regra_id": str(out.regra.id), "versao_n": out.regra.versao_n}
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo=corpo_resumo,
            )
        return Response(regra_ser, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="revogar")
    def revogar(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        regra_id = self._uuid_ou_404(pk)

        ser = RevogarRegraSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:regras:revogar",
            payload_fingerprint={"regra_id": str(regra_id)},
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                repo_regra = DjangoRegraRepository()
                uc_regra.revogar_regra(
                    uc_regra.RevogarRegraInput(
                        tenant_id=tenant_id,
                        regra_id=regra_id,
                        motivo=dados["motivo"],
                        revogado_por=usuario_id,
                        agora=datetime.now(UTC),
                    ),
                    repo=repo_regra,
                )
                _publicar_evento_precificacao(
                    acao="Precificacao.RegraRevogada",
                    payload={
                        "regra_id": str(regra_id),
                        "motivo_hash": derivar_hash_texto_canonicalizado(
                            texto=dados["motivo"], tenant_id=tenant_id
                        ),
                        "revogado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=regra_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"regra:{regra_id}",
                )
        except RuntimeError as exc:
            return _falha(
                regra_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idempotencia=novo
            )

        corpo_resumo = {"regra_id": str(regra_id), "revogada": True}
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo=corpo_resumo,
            )
        return Response(corpo_resumo, status=status.HTTP_200_OK)

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        regra_id = self._uuid_ou_404(pk)
        repo_regra = DjangoRegraRepository()
        regra = repo_regra.obter(tenant_id=tenant_id, regra_id=regra_id)
        if regra is None:
            return _falha_404(f"regra {regra_id} não encontrada")
        return Response(serializar_regra(regra, pode_ver_margem=_pode_ver_margem(request)))

    @action(detail=False, methods=["get"], url_path="vigente")
    def vigente(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        item_id_raw = request.query_params.get("item_id")
        if not item_id_raw:
            return Response(
                {"detalhe": "item_id obrigatório"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        item_id = self._uuid_ou_404(item_id_raw)
        repo_regra = DjangoRegraRepository()
        regra = repo_regra.obter_vigente(tenant_id=tenant_id, item_id=item_id, em=datetime.now(UTC))
        if regra is None:
            return _falha_404(f"regra vigente para item {item_id} não encontrada")
        return Response(serializar_regra(regra, pode_ver_margem=_pode_ver_margem(request)))


# ---------------------------------------------------------------------------
# T-PRC-035b: CalculoPrecoView (SEM Idempotency-Key — D-PRC-9 stateless)
# ---------------------------------------------------------------------------


class CalculoPrecoView(_PrecificacaoViewSetBase):
    """US-PRC-002 — calcular preços por cesta (stateless, SEM Idempotency-Key)."""

    ACTION_MAP: ClassVar[dict[str, str]] = {
        "calcular": "precificacao.calcular",
    }

    @action(detail=False, methods=["post"], url_path="calcular")
    def calcular(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = CalcularPrecosSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        try:
            repo_regra = DjangoRegraRepository()
            repo_faixa = DjangoFaixaRepository()
            repo_params = DjangoParametrosRepository()

            from src.domain.precificacao.portas import (
                CustoProviderStub,  # -- stub Wave A importado localmente para nao poluir o namespace do modulo com dependencia transitoria
            )

            agora = datetime.now(UTC)

            # D-PRC-12: resolve cliente_id → tabela_id via vínculo vigente.
            # tabela_id_cliente=None → todos os itens caem no fallback padrão.
            tabela_id_cliente: UUID | None = None
            cliente_id_parsed = UUID(str(dados["cliente_id"])) if dados.get("cliente_id") else None
            if cliente_id_parsed is not None:
                from src.infrastructure.precificacao.repositories import (  # -- import local evita ciclo infra→infra; DjangoVinculoTabelaRepository usada só neste path de calcular (molde import local consolidado)
                    DjangoVinculoTabelaRepository,
                )

                repo_vinculo = DjangoVinculoTabelaRepository()
                vinculo = repo_vinculo.obter_por_cliente(
                    tenant_id=tenant_id, cliente_id=cliente_id_parsed, em=agora
                )
                if vinculo is not None:
                    tabela_id_cliente = vinculo.tabela_id

            # Anti-N+1 (TL-PRC-14 / PERF-MÉDIO-3 P9): tabela padrão resolvida
            # UMA vez por request (constante por tenant+data_ref). O closure
            # injeta essa tabela em cada chamada de preco_para_os sem re-query.
            resolver_preco_fn = _construir_resolver_com_tabela_padrao(
                tenant_id=tenant_id,
                data_ref=agora,
            )

            resultado = uc_calculo.calcular_precos(
                uc_calculo.CalcularPrecosInput(
                    tenant_id=tenant_id,
                    itens=tuple(
                        uc_calculo.ItemCestaInput(
                            item_id=UUID(str(i["item_id"])),
                            # D-PRC-12: item pode declarar tabela_id explícita; senão
                            # herda a tabela do cliente (fallback por item em preco_para_os).
                            tabela_id=UUID(str(i["tabela_id"]))
                            if i.get("tabela_id")
                            else tabela_id_cliente,
                        )
                        for i in dados["itens"]
                    ),
                    desconto_pct=dados["desconto_pct"],
                    modo_montagem=ModoMontagem(dados["modo_montagem"]),
                    km=dados["km"],
                    parcelas=dados["parcelas"],
                    agora=agora,
                    cliente_id=cliente_id_parsed,
                ),
                repo_regra=repo_regra,
                repo_faixa=repo_faixa,
                repo_params=repo_params,
                custo_provider=CustoProviderStub(),
                resolver_preco_fn=resolver_preco_fn,
                aliquota_imposto_fn=_aliquota_imposto_fn,
            )
        except ParametrosInviaveis as exc:
            return _falha(UUID(int=0), tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except PrecoMinimoViolado as exc:
            return _falha(UUID(int=0), tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        pode_ver = _pode_ver_margem(request)
        return Response(
            serializar_resultado_calculo(resultado, pode_ver_margem=pode_ver),
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# T-PRC-035c: AprovacaoDescontoViewSet
# ---------------------------------------------------------------------------


class AprovacaoDescontoViewSet(_PrecificacaoViewSetBase):
    """US-PRC-003/004 — solicitar / decidir aprovação de desconto."""

    ACTION_MAP: ClassVar[dict[str, str]] = {
        "solicitar": "precificacao.solicitar_aprovacao",
        "decidir": "precificacao.aprovar_desconto",
        "pendentes": "precificacao.ver",
    }

    @action(detail=False, methods=["post"], url_path="solicitar")
    def solicitar(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = SolicitarAprovacaoSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:aprovacoes:solicitar",
            payload_fingerprint={
                "fingerprint_calculo": dados["fingerprint_calculo"],
                "desconto_pct": str(dados["desconto_pct"]),
                "contexto_tipo": dados["contexto_tipo"],
            },
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                repo_pedido = DjangoPedidoRepository()
                repo_faixa = DjangoFaixaRepository()

                from src.domain.precificacao.value_objects import (
                    CalculoPrecoResultado,  # -- import local evita ciclo domain.value_objects; CalculoPrecoResultado usado apenas neste path de execucao de aprovacao
                )

                eco = {
                    "km": dados["eco_km"],
                    "modo_montagem": dados["eco_modo_montagem"],
                    "parcelas": dados["eco_parcelas"],
                    "aliquota_imposto": dados["eco_aliquota_imposto"],
                }
                resultado_eco = CalculoPrecoResultado(
                    itens=(),
                    componentes_faltantes=(),
                    avisos=(),
                    alcada_exigida=Alcada.LIVRE,  # recalculado no use case
                    motor_versao=dados["motor_versao"],
                    faixas_versao=dados.get("faixas_versao") or "",
                    parametros_versao=dados["parametros_versao"],
                    imposto_ref=None,
                    eco_entradas=eco,
                )

                out = uc_aprovacao.solicitar_aprovacao(
                    uc_aprovacao.SolicitarAprovacaoInput(
                        tenant_id=tenant_id,
                        resultado_calculo=resultado_eco,
                        desconto_pct=dados["desconto_pct"],
                        contexto_tipo=ContextoTipo(dados["contexto_tipo"]),
                        solicitante_id=usuario_id,
                        agora=datetime.now(UTC),
                        contexto_id=UUID(str(dados["contexto_id"]))
                        if dados.get("contexto_id")
                        else None,
                    ),
                    repo_pedido=repo_pedido,
                    repo_faixa=repo_faixa,
                )
                pode_ver = _pode_ver_margem(request)
                pedido_ser = serializar_pedido(out.pedido, pode_ver_margem=pode_ver)

                _publicar_evento_precificacao(
                    acao="Precificacao.AprovacaoSolicitada",
                    payload={
                        "pedido_id": str(out.pedido.id),
                        "alcada_exigida": out.pedido.alcada_exigida.value,
                        "cortesia": out.pedido.cortesia,
                        "solicitante_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        # pct_solicitado NUNCA em claro (segredo comercial — INV-PRC-SEGREDO-LOG)
                    },
                    causation_id=out.pedido.id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"pedido:{out.pedido.id}",
                )

        except (DataError, IntegrityError) as exc:
            return _falha(
                UUID(int=0), tenant_id, exc, status.HTTP_409_CONFLICT, chave_idempotencia=novo
            )

        corpo_resumo = {"pedido_id": str(out.pedido.id)}
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo=corpo_resumo,
            )
        return Response(pedido_ser, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="decidir")
    def decidir(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        pedido_id = self._uuid_ou_404(pk)

        ser = DecidirAprovacaoSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        papel_decisor = _derivar_papel_decisor(request, tenant_id)

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:aprovacoes:decidir",
            payload_fingerprint={
                "pedido_id": str(pedido_id),
                "estado": dados["estado"],
            },
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                repo_pedido = DjangoPedidoRepository()
                out = uc_aprovacao.decidir_aprovacao(
                    uc_aprovacao.DecidirAprovacaoInput(
                        tenant_id=tenant_id,
                        pedido_id=pedido_id,
                        estado_novo=EstadoPedido(dados["estado"]),
                        decisor_id=usuario_id,
                        papel_decisor=papel_decisor,
                        justificativa=dados["justificativa"],
                        fingerprint_calculo_atual=dados["fingerprint_calculo_atual"],
                        agora=datetime.now(UTC),
                        hash_justificativa_fn=_hash_justificativa,
                    ),
                    repo_pedido=repo_pedido,
                    salvar_justificativa_fn=_salvar_justificativa,
                )
                _publicar_evento_precificacao(
                    acao="Precificacao.AprovacaoDecidida",
                    payload={
                        "pedido_id": str(out.pedido_id),
                        "estado": out.estado.value,
                        "justificativa_hash": out.justificativa_hash,
                        "decisor_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=pedido_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"pedido:{pedido_id}",
                )

        except uc_aprovacao.PedidoAusenteError:
            if novo is not None and novo.chave_id is not None:
                falhar_chave(
                    chave_id=novo.chave_id,
                    tenant_id=tenant_id,
                    response_status=status.HTTP_404_NOT_FOUND,
                )
            return _falha_404(f"pedido {pedido_id} não encontrado no tenant")
        except DecisorNaoIndependente as exc:
            return _falha(
                pedido_id,
                tenant_id,
                exc,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                chave_idempotencia=novo,
            )
        except AlcadaInsuficiente as exc:
            return _falha(
                pedido_id, tenant_id, exc, status.HTTP_403_FORBIDDEN, chave_idempotencia=novo
            )
        except FingerprintDivergente as exc:
            return _falha(
                pedido_id,
                tenant_id,
                exc,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                chave_idempotencia=novo,
            )
        except RuntimeError as exc:
            return _falha(
                pedido_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idempotencia=novo
            )

        corpo_resumo = {"pedido_id": str(out.pedido_id), "estado": out.estado.value}
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo=corpo_resumo,
            )
        return Response(corpo_resumo, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="pendentes")
    def pendentes(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        repo_pedido = DjangoPedidoRepository()
        pedidos = repo_pedido.listar_pendentes(tenant_id=tenant_id)
        pode_ver = _pode_ver_margem(request)
        return Response(
            [serializar_pedido(p, pode_ver_margem=pode_ver) for p in pedidos],
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# T-PRC-035d: ConfiguracaoPrecificacaoViewSet
# ---------------------------------------------------------------------------


class ConfiguracaoPrecificacaoViewSet(_PrecificacaoViewSetBase):
    """US-PRC-004 — configurar faixas, perfil de composição e parâmetros."""

    ACTION_MAP: ClassVar[dict[str, str]] = {
        "faixas": "precificacao.configurar",
        "perfil": "precificacao.configurar",
        "parametros": "precificacao.configurar",
        "listar_faixas": "precificacao.ver",
        "obter_parametros": "precificacao.ver",
    }

    @action(detail=False, methods=["post"], url_path="faixas")
    def faixas(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = ConfigurarFaixasSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:config:faixas",
            payload_fingerprint={
                "faixas": [
                    {
                        "pct_de": str(f["pct_de"]),
                        "pct_ate": str(f["pct_ate"]),
                        "alcada": f["alcada"],
                    }
                    for f in dados["faixas"]
                ]
            },
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                repo_faixa = DjangoFaixaRepository()
                faixas_finais = uc_configuracao.configurar_faixas(
                    uc_configuracao.ConfigurarFaixasInput(
                        tenant_id=tenant_id,
                        faixas=tuple(
                            uc_configuracao.FaixaInput(
                                pct_de=f["pct_de"],
                                pct_ate=f["pct_ate"],
                                alcada=Alcada(f["alcada"]),
                            )
                            for f in dados["faixas"]
                        ),
                        criado_por=usuario_id,
                    ),
                    repo_faixa=repo_faixa,
                )
                _publicar_evento_precificacao(
                    acao="Precificacao.FaixasDescontoAlteradas",
                    payload={
                        "n_faixas": len(faixas_finais),
                        "hash_conjunto": faixas_finais[0].hash_conjunto if faixas_finais else "",
                        "versao_n": faixas_finais[0].versao_n if faixas_finais else 0,
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        # valores NUNCA em claro (INV-PRC-SEGREDO-LOG)
                    },
                    causation_id=tenant_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary="faixas:replace-all",
                )
        except FaixasDescontoInvalidas as exc:
            return _falha(
                UUID(int=0),
                tenant_id,
                exc,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                chave_idempotencia=novo,
            )

        payload_resposta = [serializar_faixa(f) for f in faixas_finais]
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo={"n_faixas": len(faixas_finais)},
            )
        return Response(payload_resposta, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="perfil")
    def perfil(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = ConfigurarPerfilComposicaoSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:config:perfil",
            payload_fingerprint={"item_servico_id": str(dados["item_servico_id"])},
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                from src.infrastructure.precificacao.repositories import (
                    DjangoPerfilComposicaoRepository,  # -- import local evita referencia circular repositories→views em precificacao; DjangoPerfilComposicaoRepository usada so neste path de execucao de perfil
                )

                repo_perfil = DjangoPerfilComposicaoRepository()
                perfil_resultado = uc_configuracao.configurar_perfil_composicao(
                    uc_configuracao.ConfigurarPerfilComposicaoInput(
                        tenant_id=tenant_id,
                        item_servico_id=UUID(str(dados["item_servico_id"])),
                        componentes_esperados=tuple(
                            UUID(str(c)) for c in dados["componentes_esperados"]
                        ),
                        criado_por=usuario_id,
                        aviso_texto=dados.get("aviso_texto") or "",
                    ),
                    repo=repo_perfil,
                )
                _publicar_evento_precificacao(
                    acao="Precificacao.PerfilComposicaoAlterado",
                    payload={
                        "perfil_id": str(perfil_resultado.id),
                        "item_servico_id": str(perfil_resultado.item_servico_id),
                        "n_componentes": len(perfil_resultado.componentes_esperados),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=perfil_resultado.id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"perfil:{perfil_resultado.id}",
                )
        except (DataError, IntegrityError) as exc:
            return _falha(
                UUID(int=0), tenant_id, exc, status.HTTP_409_CONFLICT, chave_idempotencia=novo
            )

        corpo_resumo = {"perfil_id": str(perfil_resultado.id)}
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo=corpo_resumo,
            )
        return Response(corpo_resumo, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="parametros")
    def parametros(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = ConfigurarParametrosSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="precificacao:config:parametros",
            payload_fingerprint={
                "custo_km": str(dados["custo_km"]),
                "margem_alvo_default": str(dados["margem_alvo_default"]),
            },
        )
        if resp_erro is not None:
            return resp_erro

        try:
            with transaction.atomic():
                repo_params = DjangoParametrosRepository()
                params_resultado = uc_configuracao.configurar_parametros(
                    uc_configuracao.ConfigurarParametrosInput(
                        tenant_id=tenant_id,
                        custo_km=dados["custo_km"],
                        taxa_parcelamento_mensal=dados["taxa_parcelamento_mensal"],
                        pct_comissao_prevista=dados["pct_comissao_prevista"],
                        margem_alvo_default=dados["margem_alvo_default"],
                        margem_piso_default=dados["margem_piso_default"],
                        criado_por=usuario_id,
                    ),
                    repo_params=repo_params,
                )
                _publicar_evento_precificacao(
                    acao="Precificacao.ParametrosAlterados",
                    payload={
                        "params_id": str(params_resultado.id),
                        "versao_n": params_resultado.versao_n,
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        # valores NUNCA em claro (INV-PRC-SEGREDO-LOG)
                    },
                    causation_id=params_resultado.id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"params:{params_resultado.id}",
                )
        except (DataError, IntegrityError) as exc:
            return _falha(
                UUID(int=0), tenant_id, exc, status.HTTP_409_CONFLICT, chave_idempotencia=novo
            )

        pode_ver = _pode_ver_margem(request)
        payload_resposta = serializar_parametros(params_resultado, pode_ver_margem=pode_ver)
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo={"params_id": str(params_resultado.id)},
            )
        return Response(payload_resposta, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="faixas-vigentes")
    def listar_faixas(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        repo_faixa = DjangoFaixaRepository()
        faixas = repo_faixa.listar(tenant_id=tenant_id)
        return Response([serializar_faixa(f) for f in faixas], status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="parametros-vigentes")
    def obter_parametros(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        repo_params = DjangoParametrosRepository()
        params = repo_params.obter_vigentes(tenant_id=tenant_id)
        if params is None:
            return _falha_404("parâmetros de precificação não configurados")
        pode_ver = _pode_ver_margem(request)
        return Response(
            serializar_parametros(params, pode_ver_margem=pode_ver), status=status.HTTP_200_OK
        )


# ---------------------------------------------------------------------------
# VinculoTabelaClienteViewSet e _derivar_papel_decisor vivem em _views_vinculo.py
# Re-exportados aqui para compatibilidade com urls.py e imports externos.
# ---------------------------------------------------------------------------

from src.infrastructure.precificacao._views_vinculo import (  # noqa: E402, F401
    VinculoTabelaClienteViewSet,
)
