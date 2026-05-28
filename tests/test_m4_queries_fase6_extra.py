"""Tests Fase 6 M4 — 5 query services puros restantes.

- orcamento (T-CAL-107)
- historico (T-CAL-108)
- escopo (T-CAL-109)
- proficiencia (T-CAL-110)
- subcontratacao (T-CAL-111)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.queries.escopo import (
    EscopoCMCSnapshot,
)
from src.application.metrologia.calibracao.queries.escopo import (
    executar as escopo_executar,
)
from src.application.metrologia.calibracao.queries.historico import (
    executar as historico_executar,
)
from src.application.metrologia.calibracao.queries.orcamento import (
    executar as orcamento_executar,
)
from src.application.metrologia.calibracao.queries.proficiencia import (
    ImpactoNCProficienciaSnapshot,
    RodadaProficienciaSnapshot,
)
from src.application.metrologia.calibracao.queries.proficiencia import (
    executar as proficiencia_executar,
)
from src.application.metrologia.calibracao.queries.subcontratacao import (
    LaboratorioSubcontratadoSnapshot,
)
from src.application.metrologia.calibracao.queries.subcontratacao import (
    executar as subcontratacao_executar,
)
from src.domain.metrologia.calibracao.entities import (
    AvaliacaoPeriodicaSubcontratadoSnapshot,
    CalibracaoSnapshot,
    ComponenteIncertezaSnapshot,
    OrcamentoIncertezaSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    DecisaoAvaliacaoSubcontratado,
    DistribuicaoIncerteza,
    EstadoCalibracao,
    FormulaCalculoComponente,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
    TipoOrigemComponente,
)
from src.domain.metrologia.calibracao.value_objects import (
    ClassificacaoZ,
    ZonaILACG8,
)

AGORA = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


# ============================================================
# Builders
# ============================================================


def _orcamento(
    *,
    tenant: UUID | None = None,
    orc_id: UUID | None = None,
    cal_id: UUID | None = None,
    divergencia: Decimal | None = None,
    bias: Decimal | None = None,
) -> OrcamentoIncertezaSnapshot:
    return OrcamentoIncertezaSnapshot(
        id=orc_id or uuid4(),
        tenant_id=tenant or uuid4(),
        calibracao_id=cal_id or uuid4(),
        u_combinada=Decimal("0.1"),
        grau_liberdade_efetivo=Decimal("100"),
        k=Decimal("2.0"),
        U_expandida=Decimal("0.2"),
        nivel_confianca=Decimal("0.9545"),
        documentacao_agregacao="x" * 60,
        versao_motor_calculo="GUM_CLASSICO_v1 1.0.0@abc1234",
        algoritmo_1_resultado={"u_c": "0.1"},
        algoritmo_2_resultado=None,
        divergencia_pct=divergencia,
        replay_determinismo_hash="v01$h",
        bias_orcado=bias,
        bias_origem="" if bias is None else "padrao_recal",
        arredondamento_aplicado_regra="NIT_DICLA_030_2_DIGITOS_SIG",
        calculado_em=AGORA,
        correlation_id=uuid4(),
    )


def _componente(
    *,
    tenant: UUID,
    orc_id: UUID,
    nome: str,
    tipo: str = "B",
    correlato_id: UUID | None = None,
) -> ComponenteIncertezaSnapshot:
    return ComponenteIncertezaSnapshot(
        id=uuid4(),
        tenant_id=tenant,
        orcamento_incerteza_id=orc_id,
        nome_componente=nome,
        tipo_componente=tipo,
        tipo_origem_componente=TipoOrigemComponente.OUTRO,
        distribuicao=DistribuicaoIncerteza.RETANGULAR,
        divisor=Decimal("1.73205"),
        formula_calculo=FormulaCalculoComponente.OUTRO,
        valor_estimativa=Decimal("0.05"),
        contribuicao=Decimal("0.0025"),
        grau_liberdade=None if tipo == "B" else Decimal("9"),
        n_amostras=None if tipo == "B" else 10,
        s_x=None if tipo == "B" else Decimal("0.01"),
        correlacao_com_componente_id=correlato_id,
        coeficiente_correlacao=None if correlato_id is None else Decimal("0.5"),
        fonte_default_padrao_id=None,
    )


def _cal(
    *,
    tenant: UUID | None = None,
    inst_id: UUID | None = None,
    status: EstadoCalibracao = EstadoCalibracao.APROVADA,
    criada_em: datetime | None = None,
) -> CalibracaoSnapshot:
    return CalibracaoSnapshot(
        id=uuid4(),
        tenant_id=tenant or uuid4(),
        numero_interno=1,
        numero_exibido="CAL-2026-000001",
        origem_recepcao=OrigemRecepcao.AVULSA,
        atividade_os_id=None,
        instrumento_id=inst_id or uuid4(),
        snapshot_equipamento_json={},
        cliente_id=None,
        cliente_referencia_hash="v01$c",
        cliente_key_id="k",
        tipo_acreditacao=TipoAcreditacao.NAO_RBC,
        status=status,
        revision=3,
        regra_decisao=RegraDecisao.ACEITACAO_SIMPLES,
        regra_decisao_acordada_em=None,
        regra_decisao_acordada_documento_id=None,
        versao_motor_calculo="GUM_CLASSICO_v1 1.0.0@abc1234",
        procedimento_id=None,
        procedimento_versao_snapshot={},
        escopo_id=None,
        analise_critica_pedido_id=None,
        analise_critica_pedido_inline_hash="",
        capacidade_tecnica_confirmada_por_user_id=None,
        executor_id=None,
        revisor_id=None,
        conferente_id=None,
        snapshot_competencia_revisor_json=None,
        snapshot_competencia_conferente_json=None,
        excecao_2a_conf_id=None,
        zona_ilac_g8=ZonaILACG8.NA,
        decisao="NA",
        pfa_calculada=None,
        pra_calculada=None,
        subcontratado_id=None,
        aceite_subcontratacao_id=None,
        certificado_subcontratado_snapshot_json=None,
        recebedor_user_id=None,
        correlation_id=uuid4(),
        causation_id=None,
        criada_em=criada_em or AGORA - timedelta(days=1),
        criada_por_user_id=None,
    )


def _escopo(
    *,
    tenant: UUID | None = None,
    grandeza: str = "massa",
    fmin: Decimal = Decimal("0"),
    fmax: Decimal = Decimal("10"),
    rbc: bool = True,
    vig_ini: datetime | None = None,
    vig_fim: datetime | None = None,
) -> EscopoCMCSnapshot:
    return EscopoCMCSnapshot(
        id=uuid4(),
        tenant_id=tenant or uuid4(),
        grandeza=grandeza,
        faixa_min=fmin,
        faixa_max=fmax,
        unidade="kg",
        cmc_valor=Decimal("0.01"),
        cmc_unidade="kg",
        procedimento_id=None,
        rbc_acreditado=rbc,
        vigencia_inicio=vig_ini or AGORA - timedelta(days=365),
        vigencia_fim=vig_fim,
    )


def _rodada(
    *,
    tenant: UUID | None = None,
    grandeza: str = "massa",
    z: Decimal = Decimal("0.5"),
    classif: ClassificacaoZ = ClassificacaoZ.ACEITAVEL,
    rodada_em: datetime | None = None,
) -> RodadaProficienciaSnapshot:
    return RodadaProficienciaSnapshot(
        id=uuid4(),
        tenant_id=tenant or uuid4(),
        provedor="INMETRO",
        rodada_referencia="PEP-2026-001",
        grandeza=grandeza,
        valor_atribuido=Decimal("1.0"),
        valor_reportado=Decimal("1.01"),
        incerteza_reportada=Decimal("0.02"),
        incerteza_atribuida=Decimal("0.015"),
        escore_z=z,
        classificacao_z=classif,
        rodada_em=rodada_em or AGORA - timedelta(days=30),
        correlation_id=uuid4(),
    )


def _impacto(
    *,
    tenant: UUID,
    rodada_id: UUID,
    status: str = "RECALL_PENDENTE_M5",
    qtde: int = 12,
    janela_fim: datetime | None = None,
) -> ImpactoNCProficienciaSnapshot:
    return ImpactoNCProficienciaSnapshot(
        id=uuid4(),
        tenant_id=tenant,
        rodada_id=rodada_id,
        janela_inicio=AGORA - timedelta(days=180),
        janela_fim=janela_fim or AGORA - timedelta(days=10),
        status=status,
        qtde_certificados_afetados=qtde,
    )


def _lab(
    *,
    tenant: UUID | None = None,
    pais: str = "BR",
    proxima: datetime | None = None,
    score: Decimal | None = Decimal("8.5"),
    deletado: bool = False,
    vig_fim: datetime | None = None,
) -> LaboratorioSubcontratadoSnapshot:
    return LaboratorioSubcontratadoSnapshot(
        id=uuid4(),
        tenant_id=tenant or uuid4(),
        nome_legal="Lab Subcontratado X",
        pais=pais,
        score_avaliacao_atual=score,
        proxima_avaliacao_periodica_em=proxima,
        vigencia_inicio=AGORA - timedelta(days=365),
        vigencia_fim=vig_fim,
        deletado_em=AGORA - timedelta(days=10) if deletado else None,
    )


def _avaliacao(
    *,
    tenant: UUID,
    lab_id: UUID,
    avaliado_em: datetime | None = None,
) -> AvaliacaoPeriodicaSubcontratadoSnapshot:
    return AvaliacaoPeriodicaSubcontratadoSnapshot(
        id=uuid4(),
        tenant_id=tenant,
        laboratorio_id=lab_id,
        avaliado_em=avaliado_em or AGORA - timedelta(days=365),
        avaliado_por_user_id_hash="v01$Z2VyZW50ZQ==",
        score=Decimal("8.5"),
        criterios_aplicados_json={"prazo": "aprovado", "tecnico": "aprovado"},
        parecer_canonicalizado=(
            "Subcontratado avaliado conforme criterio-selecao-subcontratado-v1.0. "
            "Desempenho dentro do esperado nos 12 meses; manter credenciamento."
        ),
        parecer_hash="v01$cGFyZWNlcg==",
        decisao=DecisaoAvaliacaoSubcontratado.MANTER,
        proxima_avaliacao_em=AGORA + timedelta(days=15),
        correlation_id=uuid4(),
    )


# ============================================================
# T-CAL-107 — orcamento
# ============================================================


class TestOrcamentoQuery:
    def test_orcamento_id_mismatch_recusa(self) -> None:
        orc = _orcamento()
        with pytest.raises(ValueError, match="orcamento_id"):
            orcamento_executar(
                orcamento_id=uuid4(),
                orcamento=orc,
                componentes=[],
            )

    def test_sem_componentes(self) -> None:
        orc = _orcamento()
        res = orcamento_executar(
            orcamento_id=orc.id, orcamento=orc, componentes=[]
        )
        assert res.total_componentes == 0
        assert res.componentes_tipo_a == ()
        assert res.componentes_tipo_b == ()
        assert res.pares_correlacionados == ()
        assert res.tem_divergencia_algoritmos is False

    def test_separa_tipo_a_e_b(self) -> None:
        tenant = uuid4()
        orc = _orcamento(tenant=tenant)
        c_a = _componente(tenant=tenant, orc_id=orc.id, nome="zz_repe", tipo="A")
        c_b = _componente(tenant=tenant, orc_id=orc.id, nome="aa_temp", tipo="B")
        res = orcamento_executar(
            orcamento_id=orc.id, orcamento=orc, componentes=[c_a, c_b]
        )
        assert res.total_componentes == 2
        # ordem por nome ASC -> aa_temp primeiro
        assert res.componentes[0].id == c_b.id
        assert res.componentes[1].id == c_a.id
        assert res.componentes_tipo_a == (c_a,)
        assert res.componentes_tipo_b == (c_b,)

    def test_filtra_outro_orcamento(self) -> None:
        tenant = uuid4()
        orc = _orcamento(tenant=tenant)
        outro = _componente(tenant=tenant, orc_id=uuid4(), nome="x", tipo="B")
        res = orcamento_executar(
            orcamento_id=orc.id, orcamento=orc, componentes=[outro]
        )
        assert res.total_componentes == 0

    def test_filtra_outro_tenant(self) -> None:
        tenant = uuid4()
        orc = _orcamento(tenant=tenant)
        outro_tenant = _componente(
            tenant=uuid4(), orc_id=orc.id, nome="x", tipo="B"
        )
        res = orcamento_executar(
            orcamento_id=orc.id, orcamento=orc, componentes=[outro_tenant]
        )
        assert res.total_componentes == 0

    def test_pares_correlacionados_listados(self) -> None:
        tenant = uuid4()
        orc = _orcamento(tenant=tenant)
        c1 = _componente(tenant=tenant, orc_id=orc.id, nome="a", tipo="B")
        c2 = _componente(
            tenant=tenant, orc_id=orc.id, nome="b", tipo="B", correlato_id=c1.id
        )
        res = orcamento_executar(
            orcamento_id=orc.id, orcamento=orc, componentes=[c1, c2]
        )
        assert res.pares_correlacionados == ((c2.id, c1.id),)

    def test_divergencia_flag(self) -> None:
        orc = _orcamento(divergencia=Decimal("0.05"))
        res = orcamento_executar(
            orcamento_id=orc.id, orcamento=orc, componentes=[]
        )
        assert res.tem_divergencia_algoritmos is True

    def test_divergencia_zero_nao_flag(self) -> None:
        orc = _orcamento(divergencia=Decimal("0"))
        res = orcamento_executar(
            orcamento_id=orc.id, orcamento=orc, componentes=[]
        )
        assert res.tem_divergencia_algoritmos is False

    def test_bias_orcado_flag(self) -> None:
        orc_com = _orcamento(bias=Decimal("0.01"))
        orc_sem = _orcamento()
        r1 = orcamento_executar(
            orcamento_id=orc_com.id, orcamento=orc_com, componentes=[]
        )
        r2 = orcamento_executar(
            orcamento_id=orc_sem.id, orcamento=orc_sem, componentes=[]
        )
        assert r1.tem_bias_orcado is True
        assert r2.tem_bias_orcado is False


# ============================================================
# T-CAL-108 — historico
# ============================================================


class TestHistoricoQuery:
    def test_vazio_retorna_pagina_vazia(self) -> None:
        res = historico_executar(instrumento_id=uuid4(), calibracoes=[])
        assert res.total == 0
        assert res.itens == ()
        assert res.tem_proxima is False
        assert res.pagina == 1

    def test_ordem_decrescente_criada_em(self) -> None:
        inst = uuid4()
        velha = _cal(inst_id=inst, criada_em=AGORA - timedelta(days=30))
        nova = _cal(inst_id=inst, criada_em=AGORA - timedelta(days=1))
        res = historico_executar(
            instrumento_id=inst, calibracoes=[velha, nova]
        )
        assert res.itens[0].calibracao_id == nova.id
        assert res.itens[1].calibracao_id == velha.id

    def test_filtra_outro_instrumento(self) -> None:
        inst = uuid4()
        outra = _cal(inst_id=uuid4())
        res = historico_executar(instrumento_id=inst, calibracoes=[outra])
        assert res.total == 0

    def test_paginacao(self) -> None:
        inst = uuid4()
        cals = [
            _cal(inst_id=inst, criada_em=AGORA - timedelta(days=i))
            for i in range(1, 26)  # 25 calibracoes
        ]
        p1 = historico_executar(
            instrumento_id=inst, calibracoes=cals, pagina=1, tamanho_pagina=10
        )
        p2 = historico_executar(
            instrumento_id=inst, calibracoes=cals, pagina=2, tamanho_pagina=10
        )
        p3 = historico_executar(
            instrumento_id=inst, calibracoes=cals, pagina=3, tamanho_pagina=10
        )
        assert p1.total == 25
        assert len(p1.itens) == 10
        assert p1.tem_proxima is True
        assert len(p2.itens) == 10
        assert p2.tem_proxima is True
        assert len(p3.itens) == 5
        assert p3.tem_proxima is False

    def test_filtra_status_quando_informado(self) -> None:
        inst = uuid4()
        c1 = _cal(inst_id=inst, status=EstadoCalibracao.APROVADA)
        c2 = _cal(inst_id=inst, status=EstadoCalibracao.RECEPCIONADA)
        res = historico_executar(
            instrumento_id=inst,
            calibracoes=[c1, c2],
            status_incluir=frozenset({EstadoCalibracao.APROVADA}),
        )
        assert res.total == 1
        assert res.itens[0].calibracao_id == c1.id

    def test_filtra_tenant(self) -> None:
        inst = uuid4()
        tenant_a = uuid4()
        c_a = _cal(tenant=tenant_a, inst_id=inst)
        c_b = _cal(inst_id=inst)
        res = historico_executar(
            instrumento_id=inst, calibracoes=[c_a, c_b], tenant_id=tenant_a
        )
        assert res.total == 1
        assert res.itens[0].tenant_id == tenant_a

    def test_pagina_invalida_recusa(self) -> None:
        with pytest.raises(ValueError, match="pagina"):
            historico_executar(instrumento_id=uuid4(), calibracoes=[], pagina=0)

    def test_tamanho_invalido_recusa(self) -> None:
        with pytest.raises(ValueError, match="tamanho_pagina"):
            historico_executar(
                instrumento_id=uuid4(), calibracoes=[], tamanho_pagina=200
            )


# ============================================================
# T-CAL-109 — escopo
# ============================================================


class TestEscopoQuery:
    def test_agora_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            escopo_executar(escopos=[], em=datetime(2026, 7, 1))

    def test_filtra_grandeza(self) -> None:
        e_massa = _escopo(grandeza="massa")
        e_temp = _escopo(grandeza="temperatura")
        res = escopo_executar(
            escopos=[e_massa, e_temp], em=AGORA, grandeza="MASSA"
        )
        assert len(res) == 1
        assert res[0].grandeza == "massa"

    def test_intersecta_faixa_parcial(self) -> None:
        e = _escopo(fmin=Decimal("0"), fmax=Decimal("100"))
        # consulta 50-150 deve intersectar
        res = escopo_executar(
            escopos=[e],
            em=AGORA,
            faixa_min=Decimal("50"),
            faixa_max=Decimal("150"),
        )
        assert len(res) == 1

    def test_fora_da_faixa(self) -> None:
        e = _escopo(fmin=Decimal("0"), fmax=Decimal("100"))
        # consulta 200-300 nao intersecta
        res = escopo_executar(
            escopos=[e],
            em=AGORA,
            faixa_min=Decimal("200"),
            faixa_max=Decimal("300"),
        )
        assert res == []

    def test_apenas_rbc_filtra(self) -> None:
        e_rbc = _escopo(rbc=True)
        e_no_rbc = _escopo(rbc=False)
        res = escopo_executar(
            escopos=[e_rbc, e_no_rbc], em=AGORA, apenas_rbc=True
        )
        assert len(res) == 1
        assert res[0].rbc_acreditado is True

    def test_fora_da_vigencia(self) -> None:
        # vigencia ja expirada
        e_expirado = _escopo(
            vig_fim=AGORA - timedelta(days=10), vig_ini=AGORA - timedelta(days=365)
        )
        # ainda nao comecou
        e_futuro = _escopo(vig_ini=AGORA + timedelta(days=10))
        e_vigente = _escopo()
        res = escopo_executar(
            escopos=[e_expirado, e_futuro, e_vigente], em=AGORA
        )
        assert len(res) == 1

    def test_ordem_grandeza_faixa(self) -> None:
        e2 = _escopo(grandeza="temperatura", fmin=Decimal("0"))
        e1 = _escopo(grandeza="massa", fmin=Decimal("10"))
        e0 = _escopo(grandeza="massa", fmin=Decimal("0"))
        res = escopo_executar(escopos=[e2, e1, e0], em=AGORA)
        assert [r.escopo_id for r in res] == [e0.id, e1.id, e2.id]


# ============================================================
# T-CAL-110 — proficiencia
# ============================================================


class TestProficienciaQuery:
    def test_vazio_retorna_painel_vazio(self) -> None:
        p = proficiencia_executar(rodadas=[])
        assert p.total == 0
        assert p.total_aceitavel == 0
        assert p.total_warning == 0
        assert p.total_unacceptable == 0

    def test_contagem_classificacoes(self) -> None:
        tenant = uuid4()
        r_ok = _rodada(tenant=tenant, classif=ClassificacaoZ.ACEITAVEL)
        r_warn = _rodada(tenant=tenant, classif=ClassificacaoZ.WARNING)
        r_unaccept = _rodada(tenant=tenant, classif=ClassificacaoZ.UNACCEPTABLE)
        p = proficiencia_executar(rodadas=[r_ok, r_warn, r_unaccept])
        assert p.total == 3
        assert p.total_aceitavel == 1
        assert p.total_warning == 1
        assert p.total_unacceptable == 1

    def test_ordem_decrescente_rodada_em(self) -> None:
        tenant = uuid4()
        r_velha = _rodada(tenant=tenant, rodada_em=AGORA - timedelta(days=90))
        r_nova = _rodada(tenant=tenant, rodada_em=AGORA - timedelta(days=1))
        p = proficiencia_executar(rodadas=[r_velha, r_nova])
        assert p.linhas[0].rodada_id == r_nova.id
        assert p.linhas[1].rodada_id == r_velha.id

    def test_filtra_grandeza(self) -> None:
        r_m = _rodada(grandeza="massa")
        r_t = _rodada(grandeza="temperatura")
        p = proficiencia_executar(rodadas=[r_m, r_t], grandeza="massa")
        assert p.total == 1
        assert p.linhas[0].grandeza == "massa"

    def test_filtra_tenant(self) -> None:
        tenant_a = uuid4()
        r_a = _rodada(tenant=tenant_a)
        r_b = _rodada()
        p = proficiencia_executar(rodadas=[r_a, r_b], tenant_id=tenant_a)
        assert p.total == 1

    def test_cruza_impacto_recall(self) -> None:
        tenant = uuid4()
        r = _rodada(tenant=tenant, classif=ClassificacaoZ.UNACCEPTABLE)
        imp = _impacto(tenant=tenant, rodada_id=r.id)
        p = proficiencia_executar(rodadas=[r], impactos=[imp])
        assert p.linhas[0].impacto_status == "RECALL_PENDENTE_M5"
        assert p.linhas[0].impacto_qtde_certificados == 12
        assert p.total_com_impacto_aberto == 1

    def test_impacto_sem_recall_aberto_nao_conta(self) -> None:
        tenant = uuid4()
        r = _rodada(tenant=tenant)
        imp = _impacto(
            tenant=tenant, rodada_id=r.id, status="CONCLUIDO_SEM_RECALL"
        )
        p = proficiencia_executar(rodadas=[r], impactos=[imp])
        assert p.total_com_impacto_aberto == 0


# ============================================================
# T-CAL-111 — subcontratacao
# ============================================================


class TestSubcontratacaoQuery:
    def test_agora_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            subcontratacao_executar(
                laboratorios=[],
                agora=datetime(2026, 7, 1),
            )

    def test_vazio_retorna_lista_vazia(self) -> None:
        assert (
            subcontratacao_executar(laboratorios=[], agora=AGORA) == []
        )

    def test_classifica_vencida(self) -> None:
        lab = _lab(proxima=AGORA - timedelta(days=10))
        res = subcontratacao_executar(laboratorios=[lab], agora=AGORA)
        assert len(res) == 1
        assert res[0].status_avaliacao == "VENCIDA"
        assert res[0].dias_ate_avaliacao is not None
        assert res[0].dias_ate_avaliacao < 0

    def test_classifica_proxima_30d(self) -> None:
        lab = _lab(proxima=AGORA + timedelta(days=15))
        res = subcontratacao_executar(laboratorios=[lab], agora=AGORA)
        assert res[0].status_avaliacao == "PROXIMA_30D"

    def test_classifica_ok(self) -> None:
        lab = _lab(proxima=AGORA + timedelta(days=180))
        res = subcontratacao_executar(laboratorios=[lab], agora=AGORA)
        assert res[0].status_avaliacao == "OK"

    def test_sem_avaliacao(self) -> None:
        lab = _lab(proxima=None)
        res = subcontratacao_executar(laboratorios=[lab], agora=AGORA)
        assert res[0].status_avaliacao == "SEM_AVALIACAO"
        assert res[0].dias_ate_avaliacao is None

    def test_exclui_soft_deleted_por_default(self) -> None:
        ativo = _lab(proxima=AGORA + timedelta(days=180))
        morto = _lab(proxima=AGORA + timedelta(days=180), deletado=True)
        res = subcontratacao_executar(laboratorios=[ativo, morto], agora=AGORA)
        assert len(res) == 1
        assert res[0].laboratorio_id == ativo.id

    def test_inclui_inativos_quando_solicitado(self) -> None:
        ativo = _lab(proxima=AGORA + timedelta(days=180))
        morto = _lab(proxima=AGORA + timedelta(days=180), deletado=True)
        res = subcontratacao_executar(
            laboratorios=[ativo, morto], agora=AGORA, incluir_inativos=True
        )
        assert len(res) == 2

    def test_exclui_vigencia_fim_passado(self) -> None:
        lab_ativo = _lab(proxima=AGORA + timedelta(days=180))
        lab_expirado = _lab(
            proxima=AGORA + timedelta(days=180),
            vig_fim=AGORA - timedelta(days=1),
        )
        res = subcontratacao_executar(
            laboratorios=[lab_ativo, lab_expirado], agora=AGORA
        )
        assert len(res) == 1
        assert res[0].laboratorio_id == lab_ativo.id

    def test_filtra_pais(self) -> None:
        lab_br = _lab(proxima=AGORA + timedelta(days=180), pais="BR")
        lab_us = _lab(proxima=AGORA + timedelta(days=180), pais="US")
        res = subcontratacao_executar(
            laboratorios=[lab_br, lab_us], agora=AGORA, pais="br"
        )
        assert len(res) == 1
        assert res[0].pais == "BR"

    def test_conta_historico_avaliacoes(self) -> None:
        tenant = uuid4()
        lab = _lab(tenant=tenant, proxima=AGORA + timedelta(days=180))
        av1 = _avaliacao(tenant=tenant, lab_id=lab.id)
        av2 = _avaliacao(tenant=tenant, lab_id=lab.id)
        res = subcontratacao_executar(
            laboratorios=[lab], avaliacoes=[av1, av2], agora=AGORA
        )
        assert res[0].qtde_avaliacoes_historico == 2

    def test_ordem_vencida_primeiro_depois_proxima(self) -> None:
        venc = _lab(proxima=AGORA - timedelta(days=5))
        prox = _lab(proxima=AGORA + timedelta(days=15))
        ok = _lab(proxima=AGORA + timedelta(days=180))
        res = subcontratacao_executar(
            laboratorios=[ok, prox, venc], agora=AGORA
        )
        assert [r.laboratorio_id for r in res] == [venc.id, prox.id, ok.id]

    def test_alerta_dias_negativo_recusa(self) -> None:
        with pytest.raises(ValueError, match="alerta_dias"):
            subcontratacao_executar(
                laboratorios=[], agora=AGORA, alerta_dias=-1
            )
