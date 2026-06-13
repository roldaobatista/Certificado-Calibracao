"""Use case `calcular_precos` — porta de aplicação POR CESTA (T-PRC-031).

Stateless: não persiste nada (D-PRC-9 / INV-026). Memoização POR REQUEST
de Imposto/Parâmetros/Faixas (TL-PRC-14) — sem cache cross-request.

Consiste de:
- Resolver preço de venda via `preco_para_os(tabela_id=)` com fallback
  POR ITEM na tabela padrão (D-PRC-12).
- Buscar regras de formação vigentes.
- Buscar parâmetros, faixas e alíquota de imposto (memoizados no objeto).
- Chamar `calcular_precos` puro do domínio (D-PRC-11 — entrada canônica é a cesta).

O uso de `Imposto` vigente é SIMULAÇÃO (D-PRC-10): alíquota vigente da frente
configuracoes-sistema; "cálculo fiscal exato" é non-goal do PRD.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from src.domain.precificacao.entities import (
    FaixaAprovacaoDesconto,
    ParametrosPrecificacaoTenant,
    PerfilComposicaoPreco,
    RegraFormacaoPreco,
)
from src.domain.precificacao.enums import ModoFormacaoPreco, ModoMontagem, OrigemCusto
from src.domain.precificacao.erros import ParametrosInviaveis
from src.domain.precificacao.portas import CustoProvider
from src.domain.precificacao.repository import (
    FaixaRepository,
    ParametrosRepository,
    RegraRepository,
)
from src.domain.precificacao.transicoes import MOTOR_VERSAO
from src.domain.precificacao.transicoes import calcular_precos as _calcular_puro
from src.domain.precificacao.value_objects import CalculoPrecoResultado, Percentual
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido


@dataclass(frozen=True, slots=True)
class ItemCestaInput:
    """Representa um item na cesta de cálculo."""

    item_id: UUID
    tabela_id: UUID | None = None  # D-PRC-12: tabela específica do cliente (None = padrão)


@dataclass(frozen=True, slots=True)
class CalcularPrecosInput:
    """Entradas para calcular_precos (D-PRC-11 — entrada canônica é a CESTA)."""

    tenant_id: UUID
    itens: tuple[ItemCestaInput, ...]
    desconto_pct: Decimal  # 0..100
    modo_montagem: ModoMontagem
    km: Decimal
    parcelas: int
    agora: datetime | None = None  # None = datetime.now(UTC) — injetável em testes
    cliente_id: UUID | None = None  # para lookup de tabela via VinculoTabelaPrecoCliente


def calcular_precos(
    inp: CalcularPrecosInput,
    *,
    repo_regra: RegraRepository,
    repo_faixa: FaixaRepository,
    repo_params: ParametrosRepository,
    custo_provider: CustoProvider,
    resolver_preco_fn: ResolverPrecoFn,
    aliquota_imposto_fn: AliquotaImpostoFn,
) -> CalculoPrecoResultado:
    """Porta de aplicação `calcular_precos` POR CESTA (T-PRC-031 / D-PRC-11).

    Stateless: memoiza Imposto/Parâmetros/Faixas POR REQUEST (sem cache cross-
    request — TL-PRC-14). Consome `preco_para_os(..., tabela_id=)` com fallback
    POR ITEM na tabela padrão (D-PRC-12). Chama o motor puro do domínio.

    Args:
      inp: entradas da cesta (itens + parâmetros de contexto).
      repo_regra: repositório de RegraFormacaoPreco.
      repo_faixa: repositório de FaixaAprovacaoDesconto.
      repo_params: repositório de ParametrosPrecificacaoTenant.
      custo_provider: CustoProvider (stub Wave A → INDISPONIVEL).
      resolver_preco_fn: callable(tenant_id, item_id, tabela_id, data_ref) → PrecoResolvido.
      aliquota_imposto_fn: callable(tenant_id, data_ref) → (fracao, imposto_ref|None).

    Returns:
      CalculoPrecoResultado frozen autossuficiente para replay/carimbo (INV-026).

    Raises:
      ParametrosInviaveis: denominador ≤ 0 nas fórmulas (TL-PRC-18).
      PrecoMinimoViolado: preço final < mínimo calculável (bloqueio DURO).
    """
    agora = inp.agora if inp.agora is not None else datetime.now(UTC)

    # Memoiza por request (TL-PRC-14 / assertNumQueries)
    params: ParametrosPrecificacaoTenant | None = repo_params.obter_vigentes(
        tenant_id=inp.tenant_id
    )
    if params is None:
        raise ParametrosInviaveis(
            "Tenant sem parâmetros de precificação configurados — "
            "chame `configurar_parametros` antes de calcular."
        )

    faixas: list[FaixaAprovacaoDesconto] = repo_faixa.listar(tenant_id=inp.tenant_id)

    aliquota_fracao, imposto_ref = aliquota_imposto_fn(inp.tenant_id, agora)

    desconto_pct = Percentual(inp.desconto_pct)

    # Carrega todos os dados por item (uma query por tipo via maps — sem N+1)
    ids_itens = [i.item_id for i in inp.itens]
    tabela_id_por_item: dict[UUID, UUID | None] = {i.item_id: i.tabela_id for i in inp.itens}

    # Mapa item_id → RegraFormacaoPreco vigente (batch por ids_itens)
    regras: dict[UUID, RegraFormacaoPreco] = {}
    for item_id in ids_itens:
        r = repo_regra.obter_vigente(
            tenant_id=inp.tenant_id, item_id=item_id, em=agora
        )
        if r is not None:
            regras[item_id] = r

    # Resolve preços via porta `preco_para_os` com fallback por item (D-PRC-12)
    itens_resolvidos: list[PrecoResolvido] = []
    for item_input in inp.itens:
        preco = resolver_preco_fn(
            inp.tenant_id,
            item_input.item_id,
            tabela_id_por_item.get(item_input.item_id),
            agora,
        )
        itens_resolvidos.append(preco)

    # Custos: CUSTO_MANUAL da regra ou INDISPONIVEL via stub (D-PRC-5)
    custos: dict[UUID, Decimal | None] = {}
    origens: dict[UUID, OrigemCusto] = {}
    for item_id in ids_itens:
        regra = regras.get(item_id)
        if regra is not None and regra.modo in (
            ModoFormacaoPreco.MARGEM_ALVO, ModoFormacaoPreco.COST_PLUS
        ):
            if regra.custo_manual_declarado is not None:
                custos[item_id] = regra.custo_manual_declarado
                origens[item_id] = OrigemCusto.CUSTO_MANUAL
            else:
                # Custo via provider (COST_PLUS real ou stub)
                try:
                    custo_real = custo_provider(
                        tenant_id=inp.tenant_id, item_id=item_id
                    )
                    custos[item_id] = custo_real
                    origens[item_id] = OrigemCusto.PROVIDER_REAL
                except Exception:  # -- stub sempre levanta CustoIndisponivel; nao deve mascarar erros de logica (apenas ausencia de dado)

                    custos[item_id] = None
                    origens[item_id] = OrigemCusto.INDISPONIVEL
        else:
            custos[item_id] = None
            origens[item_id] = OrigemCusto.INDISPONIVEL

    # Perfis de composição (COMPONENTES_CHECKLIST — memoizados para a cesta)
    perfis: dict[UUID, PerfilComposicaoPreco] = {}
    # Nota: perfis são carregados sob demanda; sem repo de perfil injetado
    # neste use case (carregamento lazy no motor é responsabilidade do caller
    # de mais alto nível — Wave A entrega cesta sem perfil; COMPONENTES_CHECKLIST
    # com perfil real é GATE Wave A de orcamentos)

    return _calcular_puro(
        itens=itens_resolvidos,
        regras=regras,
        custos=custos,
        origens=origens,
        perfis=perfis,
        faixas=faixas,
        params=params,
        desconto_pct=desconto_pct,
        modo_montagem=inp.modo_montagem,
        km=inp.km,
        parcelas=inp.parcelas,
        aliquota_imposto_fracao=aliquota_fracao,
        imposto_ref=imposto_ref,
        motor_versao=MOTOR_VERSAO,
    )


# ---------------------------------------------------------------------------
# Tipos funcionais (callables injetáveis pela view)
# ---------------------------------------------------------------------------

from collections.abc import Callable  # noqa: E402 — após definição dos tipos de retorno

ResolverPrecoFn = Callable[
    [UUID, UUID, "UUID | None", datetime],
    PrecoResolvido,
]
"""Callable(tenant_id, item_id, tabela_id|None, data_ref) → PrecoResolvido.

Implementação na view: `resolver_preco_com_fallback` que chama
`query_service.preco_para_os(tabela_id=tabela_id)` e cai para
tabela padrão (fallback por item — D-PRC-12).
"""

AliquotaImpostoFn = Callable[
    [UUID, datetime],
    "tuple[Decimal, tuple[UUID, int] | None]",
]
"""Callable(tenant_id, data_ref) → (fracao_imposto, imposto_ref|None).

Implementação na view: consulta Imposto vigente da frente configuracoes-
sistema (D-PRC-10 — SIMULAÇÃO; "cálculo fiscal exato" é non-goal do PRD).
"""
