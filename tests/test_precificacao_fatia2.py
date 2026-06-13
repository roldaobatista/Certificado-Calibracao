"""Frente `precificacao` — Fatia 2 (T-PRC-038): use cases + porta + REST.

Cenários obrigatórios (spec T-PRC-038):
  1. COST_PLUS com stub ativo → 422 CustoRealIndisponivel (D-PRC-6 anti-stub)
  2. Margem não vaza sem `precificacao.ver_margem` (UNHAPPY por endpoint)
  3. Gerente decide pedido DONO → predicate nega (predicate alcada_cobre)
  4. Decisor == solicitante → DecisorNaoIndependente (INV-PRC-APROVACAO-INDEPENDENTE)
  5. Fingerprint divergente → FingerprintDivergente (D-PRC-14)
  6. Cesta multi-item (2 itens) → resultado com 2 itens calculados
  7. Fallback por item na tabela padrão (D-PRC-12)
  8. assertNumQueries: memoização POR REQUEST (TL-PRC-14)
  9. Cortesia 100% → alcada_exigida = DONO
  10. Cross-tenant 404 (RLS — sem bypass)
  11. Configurar faixas default → seed_faixas_default idempotente
  12. Configurar parâmetros → versao_n incrementa
  13. solicitar_aprovacao → PedidoAprovacaoDesconto criado com fingerprint
  14. decidir_aprovacao → one-shot SOLICITADO→APROVADO; justificativa_hash gravada

Testes puros (Fakes, sem banco) cobrem lógica de negócio.
Testes PG-real são marcados @pytest.mark.django_db (GATE-PRC-PG-REAL Wave A).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from src.domain.precificacao.entities import (
    FaixaAprovacaoDesconto,
    ParametrosPrecificacaoTenant,
    PedidoAprovacaoDesconto,
    RegraFormacaoPreco,
)
from src.domain.precificacao.enums import (
    Alcada,
    ContextoTipo,
    EstadoPedido,
    ModoFormacaoPreco,
    ModoMontagem,
)
from src.domain.precificacao.erros import (
    AlcadaInsuficiente,
    CustoRealIndisponivel,
    DecisorNaoIndependente,
    FaixasDescontoInvalidas,
    FingerprintDivergente,
)
from src.domain.precificacao.portas import (  # CustoProviderStub = alias de StubCustoProvider
    CustoProviderStub,
)
from src.domain.precificacao.value_objects import CalculoPrecoResultado, Percentual
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.produtos_pecas_servicos.enums import OrigemPreco
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import JanelaVigencia

# ---------------------------------------------------------------------------
# Constantes de teste
# ---------------------------------------------------------------------------

_T = UUID("00000000-0000-4000-8000-000000000001")  # tenant A
_T2 = UUID("00000000-0000-4000-8000-000000000002")  # tenant B (cross-tenant)
_AGORA = datetime(2026, 6, 1, tzinfo=UTC)
_JAN = datetime(2026, 1, 1, tzinfo=UTC)
_DEC = datetime(2026, 12, 31, tzinfo=UTC)
_USUARIO_A = UUID("10000000-0000-4000-8000-000000000001")
_USUARIO_B = UUID("10000000-0000-4000-8000-000000000002")

# ---------------------------------------------------------------------------
# Helpers / construtores de entidades de teste
# ---------------------------------------------------------------------------


def _vigencia(inicio=_JAN, fim=_DEC) -> JanelaVigencia:
    return JanelaVigencia(inicio=inicio, fim=fim)


def _preco_resolvido(
    preco_str: str = "100.00",
    item_id: UUID | None = None,
    tabela_id: UUID | None = None,
) -> PrecoResolvido:
    iid = item_id or uuid4()
    return PrecoResolvido(
        item_id=iid,
        item_versao_n=1,
        linha_tabela_id=uuid4(),
        tabela_id=tabela_id or uuid4(),
        preco=Preco(Decimal(preco_str)),
        data_referencia=_AGORA,
        origem_preco=OrigemPreco.MANUAL,
    )


def _params(**kwargs: Any) -> ParametrosPrecificacaoTenant:
    defaults: dict[str, Any] = {
        "custo_km": Decimal("0"),
        "taxa_parcelamento_mensal": Percentual(Decimal("0")),
        "pct_comissao_prevista": Percentual(Decimal("0")),
        "margem_alvo_default": Percentual(Decimal("20")),
        "margem_piso_default": Percentual(Decimal("5")),
    }
    defaults.update(kwargs)
    return ParametrosPrecificacaoTenant(
        id=uuid4(),
        tenant_id=_T,
        versao_n=1,
        custo_km=defaults["custo_km"],
        taxa_parcelamento_mensal=defaults["taxa_parcelamento_mensal"],
        pct_comissao_prevista=defaults["pct_comissao_prevista"],
        margem_alvo_default=defaults["margem_alvo_default"],
        margem_piso_default=defaults["margem_piso_default"],
        criado_por=uuid4(),
        criado_em=_AGORA,
    )


def _faixas_padrao(tenant_id: UUID = _T) -> list[FaixaAprovacaoDesconto]:
    return [
        FaixaAprovacaoDesconto(
            id=uuid4(), tenant_id=tenant_id,
            pct_de=Percentual(Decimal("0")),
            pct_ate=Percentual(Decimal("10")),
            alcada=Alcada.LIVRE,
            versao_n=1, hash_conjunto="abc", criado_por=uuid4(),
        ),
        FaixaAprovacaoDesconto(
            id=uuid4(), tenant_id=tenant_id,
            pct_de=Percentual(Decimal("10")),
            pct_ate=Percentual(Decimal("20")),
            alcada=Alcada.GERENTE,
            versao_n=1, hash_conjunto="abc", criado_por=uuid4(),
        ),
        FaixaAprovacaoDesconto(
            id=uuid4(), tenant_id=tenant_id,
            pct_de=Percentual(Decimal("20")),
            pct_ate=Percentual(Decimal("100")),
            alcada=Alcada.DONO,
            versao_n=1, hash_conjunto="abc", criado_por=uuid4(),
        ),
    ]


def _regra(
    item_id: UUID,
    modo: ModoFormacaoPreco = ModoFormacaoPreco.MARGEM_ALVO,
    custo_manual: str | None = "80.00",
    margem_alvo: str = "20.00",
    tenant_id: UUID = _T,
) -> RegraFormacaoPreco:
    return RegraFormacaoPreco(
        id=uuid4(),
        tenant_id=tenant_id,
        item_id=item_id,
        modo=modo,
        vigencia=_vigencia(),
        versao_n=1,
        criado_por=uuid4(),
        preco_fixo=None,
        custo_manual_declarado=Decimal(custo_manual) if custo_manual else None,
        custo_referencia_em=None,
        margem_alvo_pct=Percentual(Decimal(margem_alvo)),
        margem_piso_pct=Percentual(Decimal("5")),
    )


# ---------------------------------------------------------------------------
# Fakes (Repositórios em memória)
# ---------------------------------------------------------------------------


@dataclass
class FakeRegraRepository:
    _regras: dict[UUID, RegraFormacaoPreco] = field(default_factory=dict)
    _travar_calls: list[tuple[UUID, UUID]] = field(default_factory=list)

    def obter(self, *, tenant_id: UUID, regra_id: UUID) -> RegraFormacaoPreco | None:
        r = self._regras.get(regra_id)
        return r if r is not None and r.tenant_id == tenant_id else None

    def obter_vigente(self, *, tenant_id: UUID, item_id: UUID, em: datetime) -> RegraFormacaoPreco | None:
        for r in self._regras.values():
            if (r.tenant_id == tenant_id and r.item_id == item_id
                    and r.vigencia.inicio <= em
                    and (r.vigencia.fim is None or r.vigencia.fim > em)
                    and r.vigencia.revogado_em is None):
                return r
        return None

    def listar_por_item(self, *, tenant_id: UUID, item_id: UUID) -> list[RegraFormacaoPreco]:
        return [r for r in self._regras.values() if r.tenant_id == tenant_id and r.item_id == item_id]

    def travar_item(self, *, tenant_id: UUID, item_id: UUID) -> None:
        self._travar_calls.append((tenant_id, item_id))

    def salvar(self, regra: RegraFormacaoPreco) -> None:
        self._regras[regra.id] = regra

    def encerrar_vigencia(self, *, tenant_id: UUID, regra_id: UUID, fim: datetime) -> None:
        r = self._regras.get(regra_id)
        if r is None or r.tenant_id != tenant_id:
            raise RuntimeError(f"regra {regra_id} não encontrada")
        from dataclasses import replace
        self._regras[regra_id] = replace(r, vigencia=JanelaVigencia(
            inicio=r.vigencia.inicio, fim=fim, revogado_em=None, motivo_revogacao=None
        ))

    def revogar(self, *, tenant_id: UUID, regra_id: UUID, revogado_em: datetime, motivo: str) -> None:
        r = self._regras.get(regra_id)
        if r is None or r.tenant_id != tenant_id:
            raise RuntimeError(f"regra {regra_id} não encontrada")
        from dataclasses import replace
        self._regras[regra_id] = replace(r, vigencia=JanelaVigencia(
            inicio=r.vigencia.inicio, fim=r.vigencia.fim,
            revogado_em=revogado_em, motivo_revogacao=motivo
        ))


@dataclass
class FakeFaixaRepository:
    _faixas: list[FaixaAprovacaoDesconto] = field(default_factory=list)

    def listar(self, *, tenant_id: UUID) -> list[FaixaAprovacaoDesconto]:
        return [f for f in self._faixas if f.tenant_id == tenant_id]

    def substituir_todas(
        self, *, tenant_id: UUID, faixas: list[FaixaAprovacaoDesconto], criado_por: UUID
    ) -> None:
        self._faixas = [f for f in self._faixas if f.tenant_id != tenant_id]
        self._faixas.extend(faixas)


@dataclass
class FakePedidoRepository:
    _pedidos: dict[UUID, PedidoAprovacaoDesconto] = field(default_factory=dict)

    def obter(self, *, tenant_id: UUID, pedido_id: UUID) -> PedidoAprovacaoDesconto | None:
        p = self._pedidos.get(pedido_id)
        return p if p is not None and p.tenant_id == tenant_id else None

    def listar_pendentes(self, *, tenant_id: UUID) -> list[PedidoAprovacaoDesconto]:
        return [
            p for p in self._pedidos.values()
            if p.tenant_id == tenant_id and p.estado == EstadoPedido.SOLICITADO
        ]

    def salvar(self, pedido: PedidoAprovacaoDesconto) -> None:
        self._pedidos[pedido.id] = pedido

    def decidir(
        self, *, tenant_id: UUID, pedido_id: UUID, estado: EstadoPedido,
        decisor_id: UUID, justificativa_hash: str, decidido_em: datetime
    ) -> None:
        p = self._pedidos.get(pedido_id)
        if p is None or p.tenant_id != tenant_id or p.estado != EstadoPedido.SOLICITADO:
            raise RuntimeError(f"pedido {pedido_id} não está SOLICITADO ou não existe.")
        from dataclasses import replace
        self._pedidos[pedido_id] = replace(
            p, estado=estado, decisor_id=decisor_id,
            justificativa_hash=justificativa_hash, decidido_em=decidido_em
        )


@dataclass
class FakeParametrosRepository:
    _params: ParametrosPrecificacaoTenant | None = None
    _queries: int = 0

    def obter_vigentes(self, *, tenant_id: UUID) -> ParametrosPrecificacaoTenant | None:
        self._queries += 1
        return self._params

    def salvar(self, parametros: ParametrosPrecificacaoTenant) -> None:
        self._params = parametros


# ---------------------------------------------------------------------------
# 1. COST_PLUS com stub → 422 CustoRealIndisponivel (D-PRC-6 anti-stub)
# ---------------------------------------------------------------------------


def test_publicar_regra_cost_plus_stub_levanta_custo_real_indisponivel() -> None:
    """D-PRC-6: COST_PLUS sem custo_manual_declarado + stub ativo → CustoRealIndisponivel."""
    from src.application.precificacao.regra import PublicarRegraInput, publicar_regra

    repo = FakeRegraRepository()
    item_id = uuid4()

    inp = PublicarRegraInput(
        tenant_id=_T,
        item_id=item_id,
        modo="cost_plus",
        criado_por=_USUARIO_A,
        agora=_AGORA,
        vigencia_inicio=_JAN,
        preco_fixo=None,
        custo_manual_declarado=None,  # sem custo manual → stub ativado
        custo_referencia_em=None,
        margem_alvo_pct=Decimal("20"),
        margem_piso_pct=Decimal("5"),
    )

    with pytest.raises(CustoRealIndisponivel):
        publicar_regra(inp, repo=repo, custo_provider=CustoProviderStub())


# ---------------------------------------------------------------------------
# 2. Filtrar margem — sem permissão, campos restritos são removidos
# ---------------------------------------------------------------------------


def test_filtrar_visao_margem_remove_campos_restritos_sem_permissao() -> None:
    """D-PRC-4 / INV-PRC-MARGEM-RBAC: sem ver_margem → margem_estimada e custo_estimado removidos."""
    from src.infrastructure.precificacao.serializers import filtrar_visao_margem

    payload = {
        "semaforo": "verde",
        "preco_minimo": "80.00",
        "margem_estimada": "20.00",
        "custo_estimado": "80.00",
        "preco_final": "100.00",
    }
    resultado = filtrar_visao_margem(payload, pode_ver_margem=False)
    assert "margem_estimada" not in resultado
    assert "custo_estimado" not in resultado
    assert "semaforo" in resultado
    assert "preco_minimo" in resultado
    assert "preco_final" in resultado


def test_filtrar_visao_margem_mantem_campos_com_permissao() -> None:
    """D-PRC-4: com ver_margem → todos os campos visíveis."""
    from src.infrastructure.precificacao.serializers import filtrar_visao_margem

    payload = {
        "semaforo": "verde",
        "preco_minimo": "80.00",
        "margem_estimada": "20.00",
        "custo_estimado": "80.00",
    }
    resultado = filtrar_visao_margem(payload, pode_ver_margem=True)
    assert resultado == payload


# ---------------------------------------------------------------------------
# 3. Gerente decide pedido DONO → AlcadaInsuficiente
# ---------------------------------------------------------------------------


def test_decidir_aprovacao_gerente_nao_pode_decidir_alcada_dono() -> None:
    """Predicate alcada_cobre: papel GERENTE não cobre alçada DONO (T-PRC-036)."""
    from src.application.precificacao.aprovacao import (
        DecidirAprovacaoInput,
        decidir_aprovacao,
    )

    # Cria pedido com alçada DONO
    pedido = PedidoAprovacaoDesconto(
        id=uuid4(),
        tenant_id=_T,
        contexto_tipo=ContextoTipo.AVULSO,
        contexto_id=None,
        pct_solicitado=Percentual(Decimal("25")),
        cortesia=False,
        alcada_exigida=Alcada.DONO,
        fingerprint_calculo="fp_teste_01234567890123456789012345678901234567890123456789012345",
        estado=EstadoPedido.SOLICITADO,
        solicitante_id=_USUARIO_A,
        snapshot_probatorio="{}",
        criado_em=_AGORA,
    )
    repo_pedido = FakePedidoRepository()
    repo_pedido.salvar(pedido)

    justificativas_salvas: list[tuple[UUID, UUID, str]] = []

    with pytest.raises(AlcadaInsuficiente):
        decidir_aprovacao(
            DecidirAprovacaoInput(
                tenant_id=_T,
                pedido_id=pedido.id,
                estado_novo=EstadoPedido.APROVADO,
                decisor_id=_USUARIO_B,  # usuário diferente
                papel_decisor=Alcada.GERENTE,  # GERENTE não cobre DONO
                justificativa="Justificativa de aprovação suficientemente longa",
                fingerprint_calculo_atual=pedido.fingerprint_calculo,
                agora=_AGORA,
                hash_justificativa_fn=lambda t, _tid: f"hash:{t[:8]}",
            ),
            repo_pedido=repo_pedido,
            salvar_justificativa_fn=lambda pid, tid, txt: justificativas_salvas.append((pid, tid, txt)),
        )


# ---------------------------------------------------------------------------
# 4. Decisor == solicitante → DecisorNaoIndependente
# ---------------------------------------------------------------------------


def test_decidir_aprovacao_decisor_igual_solicitante_recusado() -> None:
    """INV-PRC-APROVACAO-INDEPENDENTE: decisor == solicitante → DecisorNaoIndependente."""
    from src.application.precificacao.aprovacao import (
        DecidirAprovacaoInput,
        decidir_aprovacao,
    )

    pedido = PedidoAprovacaoDesconto(
        id=uuid4(),
        tenant_id=_T,
        contexto_tipo=ContextoTipo.AVULSO,
        contexto_id=None,
        pct_solicitado=Percentual(Decimal("15")),
        cortesia=False,
        alcada_exigida=Alcada.GERENTE,
        fingerprint_calculo="fp_teste_01234567890123456789012345678901234567890123456789012345",
        estado=EstadoPedido.SOLICITADO,
        solicitante_id=_USUARIO_A,
        snapshot_probatorio="{}",
        criado_em=_AGORA,
    )
    repo_pedido = FakePedidoRepository()
    repo_pedido.salvar(pedido)

    with pytest.raises(DecisorNaoIndependente):
        decidir_aprovacao(
            DecidirAprovacaoInput(
                tenant_id=_T,
                pedido_id=pedido.id,
                estado_novo=EstadoPedido.APROVADO,
                decisor_id=_USUARIO_A,  # MESMO que solicitante_id
                papel_decisor=Alcada.DONO,
                justificativa="Justificativa suficientemente longa para o teste",
                fingerprint_calculo_atual=pedido.fingerprint_calculo,
                agora=_AGORA,
                hash_justificativa_fn=lambda t, _tid: f"hash:{t[:8]}",
            ),
            repo_pedido=repo_pedido,
            salvar_justificativa_fn=lambda pid, tid, txt: None,
        )


# ---------------------------------------------------------------------------
# 5. Fingerprint divergente → FingerprintDivergente
# ---------------------------------------------------------------------------


def test_decidir_aprovacao_fingerprint_divergente_recusado() -> None:
    """D-PRC-14: fingerprint_calculo_atual != pedido.fingerprint_calculo → FingerprintDivergente."""
    from src.application.precificacao.aprovacao import (
        DecidirAprovacaoInput,
        decidir_aprovacao,
    )

    fp_original = "a" * 64
    fp_novo = "b" * 64

    pedido = PedidoAprovacaoDesconto(
        id=uuid4(),
        tenant_id=_T,
        contexto_tipo=ContextoTipo.AVULSO,
        contexto_id=None,
        pct_solicitado=Percentual(Decimal("15")),
        cortesia=False,
        alcada_exigida=Alcada.GERENTE,
        fingerprint_calculo=fp_original,
        estado=EstadoPedido.SOLICITADO,
        solicitante_id=_USUARIO_A,
        snapshot_probatorio="{}",
        criado_em=_AGORA,
    )
    repo_pedido = FakePedidoRepository()
    repo_pedido.salvar(pedido)

    with pytest.raises(FingerprintDivergente):
        decidir_aprovacao(
            DecidirAprovacaoInput(
                tenant_id=_T,
                pedido_id=pedido.id,
                estado_novo=EstadoPedido.APROVADO,
                decisor_id=_USUARIO_B,
                papel_decisor=Alcada.DONO,
                justificativa="Justificativa suficientemente longa para o teste",
                fingerprint_calculo_atual=fp_novo,  # DIVERGE do original
                agora=_AGORA,
                hash_justificativa_fn=lambda t, _tid: f"hash:{t[:8]}",
            ),
            repo_pedido=repo_pedido,
            salvar_justificativa_fn=lambda pid, tid, txt: None,
        )


# ---------------------------------------------------------------------------
# 6. Cesta multi-item (2 itens)
# ---------------------------------------------------------------------------


def test_calcular_precos_cesta_dois_itens() -> None:
    """D-PRC-11: cesta com 2 itens retorna 2 ItemCalculado no resultado."""
    from src.application.precificacao.calculo import (
        CalcularPrecosInput,
        ItemCestaInput,
        calcular_precos,
    )

    item1_id = uuid4()
    item2_id = uuid4()

    repo_regra = FakeRegraRepository()
    repo_regra.salvar(_regra(item1_id, modo=ModoFormacaoPreco.PRECO_FIXO, custo_manual=None))
    repo_regra.salvar(_regra(item2_id, modo=ModoFormacaoPreco.PRECO_FIXO, custo_manual=None))

    repo_faixa = FakeFaixaRepository()
    repo_faixa._faixas = _faixas_padrao()

    repo_params = FakeParametrosRepository()
    repo_params._params = _params()

    precos = {item1_id: "100.00", item2_id: "200.00"}

    def _resolver(tid: UUID, iid: UUID, tid_tabela: UUID | None, dt: datetime) -> PrecoResolvido:
        return _preco_resolvido(preco_str=precos.get(iid, "100.00"), item_id=iid)

    resultado = calcular_precos(
        CalcularPrecosInput(
            tenant_id=_T,
            itens=(ItemCestaInput(item_id=item1_id), ItemCestaInput(item_id=item2_id)),
            desconto_pct=Decimal("0"),
            modo_montagem=ModoMontagem.FECHADO_COM_AVISO,
            km=Decimal("0"),
            parcelas=1,
            agora=_AGORA,
        ),
        repo_regra=repo_regra,
        repo_faixa=repo_faixa,
        repo_params=repo_params,
        custo_provider=CustoProviderStub(),
        resolver_preco_fn=_resolver,
        aliquota_imposto_fn=lambda tid, dt: (Decimal("0"), None),
    )

    assert len(resultado.itens) == 2
    item_ids_resultado = {str(item.preco_base.item_id) for item in resultado.itens}
    assert str(item1_id) in item_ids_resultado
    assert str(item2_id) in item_ids_resultado


# ---------------------------------------------------------------------------
# 7. Fallback por item na tabela padrão (D-PRC-12)
# ---------------------------------------------------------------------------


def test_calcular_precos_fallback_tabela_padrao_por_item() -> None:
    """D-PRC-12: tabela_id=None → cai para tabela padrão (não viola ADR-0081).

    O `resolver_preco_fn` é chamado com tabela_id=None → implementação da view
    usa `preco_para_os(tabela_id=None)` que vai à tabela padrão (fail-closed 422
    se nem a padrão tiver linha — D-PPS-3).
    """
    from src.application.precificacao.calculo import (
        CalcularPrecosInput,
        ItemCestaInput,
        calcular_precos,
    )

    item_id = uuid4()
    tabela_padrao_id = uuid4()
    resolver_calls: list[UUID | None] = []

    def _resolver_rastreador(tid: UUID, iid: UUID, tid_tabela: UUID | None, dt: datetime) -> PrecoResolvido:
        resolver_calls.append(tid_tabela)
        return _preco_resolvido(preco_str="150.00", item_id=iid, tabela_id=tabela_padrao_id)

    repo_regra = FakeRegraRepository()
    repo_faixa = FakeFaixaRepository()
    repo_faixa._faixas = _faixas_padrao()
    repo_params = FakeParametrosRepository()
    repo_params._params = _params()

    calcular_precos(
        CalcularPrecosInput(
            tenant_id=_T,
            itens=(ItemCestaInput(item_id=item_id, tabela_id=None),),  # SEM tabela específica
            desconto_pct=Decimal("0"),
            modo_montagem=ModoMontagem.FECHADO_COM_AVISO,
            km=Decimal("0"),
            parcelas=1,
            agora=_AGORA,
        ),
        repo_regra=repo_regra,
        repo_faixa=repo_faixa,
        repo_params=repo_params,
        custo_provider=CustoProviderStub(),
        resolver_preco_fn=_resolver_rastreador,
        aliquota_imposto_fn=lambda tid, dt: (Decimal("0"), None),
    )

    # Verificar que tabela_id=None foi passado (fallback delegado ao query_service)
    assert resolver_calls == [None], f"Esperava tabela_id=None, recebeu {resolver_calls}"


# ---------------------------------------------------------------------------
# 8. Memoização por request (TL-PRC-14 / assertNumQueries)
# ---------------------------------------------------------------------------


def test_calcular_precos_memoiza_params_e_faixas_por_request() -> None:
    """TL-PRC-14: Params e Faixas são carregados EXATAMENTE 1x por chamada de calcular_precos.

    O FakeParametrosRepository rastreia queries para validar memoização.
    """
    from src.application.precificacao.calculo import (
        CalcularPrecosInput,
        ItemCestaInput,
        calcular_precos,
    )

    item1_id = uuid4()
    item2_id = uuid4()

    repo_params = FakeParametrosRepository()
    repo_params._params = _params()

    repo_faixa_spy = FakeFaixaRepository()
    repo_faixa_spy._faixas = _faixas_padrao()

    listar_calls: list[str] = []
    original_listar = repo_faixa_spy.listar

    def _listar_spy(*, tenant_id: UUID) -> list[FaixaAprovacaoDesconto]:
        listar_calls.append(str(tenant_id))
        return original_listar(tenant_id=tenant_id)

    repo_faixa_spy.listar = _listar_spy  # type: ignore[method-assign]

    repo_regra = FakeRegraRepository()

    calcular_precos(
        CalcularPrecosInput(
            tenant_id=_T,
            itens=(ItemCestaInput(item_id=item1_id), ItemCestaInput(item_id=item2_id)),
            desconto_pct=Decimal("0"),
            modo_montagem=ModoMontagem.FECHADO_COM_AVISO,
            km=Decimal("0"),
            parcelas=1,
            agora=_AGORA,
        ),
        repo_regra=repo_regra,
        repo_faixa=repo_faixa_spy,
        repo_params=repo_params,
        custo_provider=CustoProviderStub(),
        resolver_preco_fn=lambda tid, iid, tb, dt: _preco_resolvido(item_id=iid),
        aliquota_imposto_fn=lambda tid, dt: (Decimal("0"), None),
    )

    # Params: exatamente 1 query (memoizado)
    assert repo_params._queries == 1, f"Esperava 1 query params, encontrou {repo_params._queries}"
    # Faixas: exatamente 1 chamada listar (memoizada antes do motor puro)
    assert len(listar_calls) == 1, f"Esperava 1 call faixas, encontrou {len(listar_calls)}"


# ---------------------------------------------------------------------------
# 9. Cortesia 100% → alcada_exigida = DONO
# ---------------------------------------------------------------------------


def test_solicitar_aprovacao_cortesia_exige_alcada_dono() -> None:
    """D-PRC-13: cortesia 100% → alcada_exigida = DONO, obrigatório."""
    from src.application.precificacao.aprovacao import (
        SolicitarAprovacaoInput,
        solicitar_aprovacao,
    )

    repo_pedido = FakePedidoRepository()
    repo_faixa = FakeFaixaRepository()
    repo_faixa._faixas = _faixas_padrao()

    eco = {"km": "0", "modo_montagem": "fechado_com_aviso", "parcelas": "1", "aliquota_imposto": "0"}
    resultado_eco = CalculoPrecoResultado(
        itens=(),
        componentes_faltantes=frozenset(),
        avisos=(),
        alcada_exigida=Alcada.LIVRE,
        motor_versao="v1",
        faixas_versao="abc",
        parametros_versao=1,
        imposto_ref=None,
        eco_entradas=eco,
    )

    out = solicitar_aprovacao(
        SolicitarAprovacaoInput(
            tenant_id=_T,
            resultado_calculo=resultado_eco,
            desconto_pct=Decimal("100"),  # CORTESIA
            contexto_tipo=ContextoTipo.AVULSO,
            solicitante_id=_USUARIO_A,
            agora=_AGORA,
        ),
        repo_pedido=repo_pedido,
        repo_faixa=repo_faixa,
    )

    assert out.pedido.cortesia is True
    assert out.pedido.alcada_exigida == Alcada.DONO


# ---------------------------------------------------------------------------
# 10. Cross-tenant isolamento (sem RLS real — simulado via Fakes)
# ---------------------------------------------------------------------------


def test_cross_tenant_retorna_none_em_pedido() -> None:
    """RLS: pedido de tenant A não visível para tenant B (FakeRepository simula via tenant_id)."""
    from src.application.precificacao.aprovacao import (
        DecidirAprovacaoInput,
        PedidoAusenteError,
        decidir_aprovacao,
    )

    pedido = PedidoAprovacaoDesconto(
        id=uuid4(),
        tenant_id=_T,  # tenant A
        contexto_tipo=ContextoTipo.AVULSO,
        contexto_id=None,
        pct_solicitado=Percentual(Decimal("15")),
        cortesia=False,
        alcada_exigida=Alcada.GERENTE,
        fingerprint_calculo="a" * 64,
        estado=EstadoPedido.SOLICITADO,
        solicitante_id=_USUARIO_A,
        snapshot_probatorio="{}",
        criado_em=_AGORA,
    )
    repo_pedido = FakePedidoRepository()
    repo_pedido.salvar(pedido)

    with pytest.raises(PedidoAusenteError):
        decidir_aprovacao(
            DecidirAprovacaoInput(
                tenant_id=_T2,  # tenant B — cross-tenant
                pedido_id=pedido.id,
                estado_novo=EstadoPedido.APROVADO,
                decisor_id=_USUARIO_B,
                papel_decisor=Alcada.DONO,
                justificativa="Justificativa suficientemente longa para o teste",
                fingerprint_calculo_atual="a" * 64,
                agora=_AGORA,
                hash_justificativa_fn=lambda t, _tid: f"hash:{t[:8]}",
            ),
            repo_pedido=repo_pedido,
            salvar_justificativa_fn=lambda pid, tid, txt: None,
        )


# ---------------------------------------------------------------------------
# 11. seed_faixas_default idempotente
# ---------------------------------------------------------------------------


def test_seed_faixas_default_idempotente() -> None:
    """D-PRC-3 / TL-PRC-15: seed_faixas_default chamado 2x → mesmo resultado, sem duplicar."""
    from src.application.precificacao.configuracao import seed_faixas_default

    repo = FakeFaixaRepository()

    # 1ª chamada — seed
    faixas1 = seed_faixas_default(
        tenant_id=_T, criado_por=_USUARIO_A, repo_faixa=repo
    )
    assert len(faixas1) == 3

    # 2ª chamada — idempotente (retorna existentes sem alterar)
    faixas2 = seed_faixas_default(
        tenant_id=_T, criado_por=_USUARIO_A, repo_faixa=repo
    )
    assert len(faixas2) == 3
    # Sem duplicatas no repositório
    assert len(repo.listar(tenant_id=_T)) == 3


# ---------------------------------------------------------------------------
# 12. configurar_faixas — versao_n incrementa; faixas inválidas levantam erro
# ---------------------------------------------------------------------------


def test_configurar_faixas_incrementa_versao_n() -> None:
    """TL-PRC-16: configurar_faixas incrementa versao_n a cada replace-all."""
    from src.application.precificacao.configuracao import (
        ConfigurarFaixasInput,
        FaixaInput,
        configurar_faixas,
    )

    repo = FakeFaixaRepository()
    repo._faixas = _faixas_padrao()  # versao_n=1 já existente

    novas = configurar_faixas(
        ConfigurarFaixasInput(
            tenant_id=_T,
            faixas=(
                FaixaInput(pct_de=Decimal("0"), pct_ate=Decimal("15"), alcada=Alcada.LIVRE),
                FaixaInput(pct_de=Decimal("15"), pct_ate=Decimal("100"), alcada=Alcada.GERENTE),
            ),
            criado_por=_USUARIO_A,
        ),
        repo_faixa=repo,
    )

    assert all(f.versao_n == 2 for f in novas), "Versao_n deve ser 2 (max existente + 1)"
    assert len(novas) == 2


def test_configurar_faixas_invalidas_levanta_erro() -> None:
    """INV-PRC-FAIXAS-CONTIGUAS: faixas com buraco → FaixasDescontoInvalidas."""
    from src.application.precificacao.configuracao import (
        ConfigurarFaixasInput,
        FaixaInput,
        configurar_faixas,
    )

    repo = FakeFaixaRepository()

    with pytest.raises(FaixasDescontoInvalidas):
        configurar_faixas(
            ConfigurarFaixasInput(
                tenant_id=_T,
                faixas=(
                    FaixaInput(pct_de=Decimal("0"), pct_ate=Decimal("10"), alcada=Alcada.LIVRE),
                    # Buraco de 10 a 20 (falta a faixa do meio)
                    FaixaInput(pct_de=Decimal("20"), pct_ate=Decimal("100"), alcada=Alcada.DONO),
                ),
                criado_por=_USUARIO_A,
            ),
            repo_faixa=repo,
        )


# ---------------------------------------------------------------------------
# 13. solicitar_aprovacao → PedidoAprovacaoDesconto criado com fingerprint
# ---------------------------------------------------------------------------


def test_solicitar_aprovacao_cria_pedido_com_fingerprint() -> None:
    """US-PRC-003: solicitar_aprovacao persiste pedido com fingerprint canônico."""
    from src.application.precificacao.aprovacao import (
        SolicitarAprovacaoInput,
        solicitar_aprovacao,
    )

    repo_pedido = FakePedidoRepository()
    repo_faixa = FakeFaixaRepository()
    repo_faixa._faixas = _faixas_padrao()

    eco = {"km": "10", "modo_montagem": "fechado_com_aviso", "parcelas": "1", "aliquota_imposto": "0.05"}
    resultado_eco = CalculoPrecoResultado(
        itens=(),
        componentes_faltantes=frozenset(),
        avisos=(),
        alcada_exigida=Alcada.GERENTE,
        motor_versao="v1",
        faixas_versao="abc",
        parametros_versao=1,
        imposto_ref=None,
        eco_entradas=eco,
    )

    out = solicitar_aprovacao(
        SolicitarAprovacaoInput(
            tenant_id=_T,
            resultado_calculo=resultado_eco,
            desconto_pct=Decimal("15"),  # faixa GERENTE
            contexto_tipo=ContextoTipo.ORCAMENTO,
            solicitante_id=_USUARIO_A,
            agora=_AGORA,
            contexto_id=uuid4(),
        ),
        repo_pedido=repo_pedido,
        repo_faixa=repo_faixa,
    )

    assert out.pedido.alcada_exigida == Alcada.GERENTE
    assert out.pedido.estado == EstadoPedido.SOLICITADO
    assert len(out.pedido.fingerprint_calculo) == 64  # SHA-256 hex
    assert out.pedido.tenant_id == _T
    assert out.pedido.solicitante_id == _USUARIO_A
    # Pedido deve estar salvo no repositório
    salvo = repo_pedido.obter(tenant_id=_T, pedido_id=out.pedido.id)
    assert salvo is not None


# ---------------------------------------------------------------------------
# 14. decidir_aprovacao one-shot SOLICITADO → APROVADO; justificativa_hash gravada
# ---------------------------------------------------------------------------


def test_decidir_aprovacao_one_shot_salva_justificativa_hash() -> None:
    """US-PRC-004 / D-PRC-15: one-shot SOLICITADO→APROVADO + justificativa_hash no pedido."""
    from src.application.precificacao.aprovacao import (
        DecidirAprovacaoInput,
        decidir_aprovacao,
    )

    fp = "c" * 64
    pedido = PedidoAprovacaoDesconto(
        id=uuid4(),
        tenant_id=_T,
        contexto_tipo=ContextoTipo.AVULSO,
        contexto_id=None,
        pct_solicitado=Percentual(Decimal("15")),
        cortesia=False,
        alcada_exigida=Alcada.GERENTE,
        fingerprint_calculo=fp,
        estado=EstadoPedido.SOLICITADO,
        solicitante_id=_USUARIO_A,
        snapshot_probatorio="{}",
        criado_em=_AGORA,
    )
    repo_pedido = FakePedidoRepository()
    repo_pedido.salvar(pedido)

    justificativas_salvas: list[tuple[UUID, UUID, str]] = []

    out = decidir_aprovacao(
        DecidirAprovacaoInput(
            tenant_id=_T,
            pedido_id=pedido.id,
            estado_novo=EstadoPedido.APROVADO,
            decisor_id=_USUARIO_B,
            papel_decisor=Alcada.DONO,
            justificativa="Aprovado: análise concluída satisfatoriamente",
            fingerprint_calculo_atual=fp,
            agora=_AGORA,
            hash_justificativa_fn=lambda texto, tid: f"hash256:{texto[:6]}",
        ),
        repo_pedido=repo_pedido,
        salvar_justificativa_fn=lambda pid, tid, txt: justificativas_salvas.append((pid, tid, txt)),
    )

    assert out.estado == EstadoPedido.APROVADO
    assert out.justificativa_hash == "hash256:Aprova"
    assert len(justificativas_salvas) == 1
    assert justificativas_salvas[0][0] == pedido.id

    # Estado no repositório deve ser APROVADO
    salvo = repo_pedido.obter(tenant_id=_T, pedido_id=pedido.id)
    assert salvo is not None
    assert salvo.estado == EstadoPedido.APROVADO

    # One-shot: segunda chamada deve falhar
    with pytest.raises(RuntimeError):
        decidir_aprovacao(
            DecidirAprovacaoInput(
                tenant_id=_T,
                pedido_id=pedido.id,
                estado_novo=EstadoPedido.NEGADO,
                decisor_id=_USUARIO_B,
                papel_decisor=Alcada.DONO,
                justificativa="Segunda tentativa não deve funcionar",
                fingerprint_calculo_atual=fp,
                agora=_AGORA,
                hash_justificativa_fn=lambda t, _tid: f"hash:{t[:6]}",
            ),
            repo_pedido=repo_pedido,
            salvar_justificativa_fn=lambda pid, tid, txt: None,
        )


# ---------------------------------------------------------------------------
# 15. configurar_parametros → versao_n incrementa
# ---------------------------------------------------------------------------


def test_configurar_parametros_incrementa_versao_n() -> None:
    """D-PRC-9 versionado: cada configurar_parametros gera versao_n = anterior + 1."""
    from src.application.precificacao.configuracao import (
        ConfigurarParametrosInput,
        configurar_parametros,
    )

    repo_params = FakeParametrosRepository()
    repo_params._params = _params()  # versao_n=1

    params_v2 = configurar_parametros(
        ConfigurarParametrosInput(
            tenant_id=_T,
            custo_km=Decimal("2.50"),
            taxa_parcelamento_mensal=Decimal("1.5"),
            pct_comissao_prevista=Decimal("5.0"),
            margem_alvo_default=Decimal("25.0"),
            margem_piso_default=Decimal("8.0"),
            criado_por=_USUARIO_A,
        ),
        repo_params=repo_params,
    )

    assert params_v2.versao_n == 2
    assert params_v2.custo_km == Decimal("2.50")


# ---------------------------------------------------------------------------
# 16. ACOES_PRECIFICACAO registradas no ACOES_CANONICAS
# ---------------------------------------------------------------------------


def test_acoes_precificacao_em_acoes_canonicas() -> None:
    """T-PRC-037: ACOES_PRECIFICACAO incluídas em ACOES_CANONICAS."""
    from src.infrastructure.audit.acoes_canonicas import ACOES_CANONICAS, ACOES_PRECIFICACAO

    for acao in ACOES_PRECIFICACAO:
        assert acao in ACOES_CANONICAS, f"Ação {acao!r} ausente em ACOES_CANONICAS"


# ---------------------------------------------------------------------------
# 17. Predicate alcada_cobre registrado em apps.ready()
# ---------------------------------------------------------------------------


def test_predicate_alcada_cobre_registrado() -> None:
    """T-PRC-036: predicate `alcada_cobre` deve estar no registry após apps.ready()."""
    from src.infrastructure.authz.predicates import get_predicates

    predicates = get_predicates()
    assert "alcada_cobre" in predicates, "predicate 'alcada_cobre' não registrado"
    pred = predicates["alcada_cobre"]
    assert "precificacao.aprovar_desconto" in pred.actions


def test_predicate_alcada_cobre_logica_correta() -> None:
    """T-PRC-036: lógica do predicate alcada_cobre — DONO cobre tudo; LIVRE cobre só LIVRE."""
    from src.infrastructure.authz.predicates import get_predicates

    predicates = get_predicates()
    fn = predicates["alcada_cobre"].fn

    # DONO cobre DONO
    allowed, _ = fn({"alcada_exigida": "dono", "papel_do_decisor": "dono"})
    assert allowed is True

    # GERENTE NÃO cobre DONO
    allowed, reason = fn({"alcada_exigida": "dono", "papel_do_decisor": "gerente"})
    assert allowed is False
    assert "AlcadaInsuficiente" in reason

    # DONO cobre GERENTE
    allowed, _ = fn({"alcada_exigida": "gerente", "papel_do_decisor": "dono"})
    assert allowed is True

    # LIVRE não cobre GERENTE
    allowed, reason = fn({"alcada_exigida": "gerente", "papel_do_decisor": "livre"})
    assert allowed is False
