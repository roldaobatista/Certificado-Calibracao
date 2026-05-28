"""Tests Fase 7 restante (Batch T):
- T-CAL-119 analisar_correlacao_componentes
- T-CAL-120 geo_truncamento_calibracao_5a
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.jobs.analisar_correlacao_componentes import (
    executar as analisar_correl_executar,
)
from src.application.metrologia.calibracao.jobs.geo_truncamento_calibracao_5a import (
    executar as geo_trunc_executar,
)
from src.domain.metrologia.calibracao.entities import (
    CalibracaoSnapshot,
    ComponenteIncertezaSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    DistribuicaoIncerteza,
    EstadoCalibracao,
    FormulaCalculoComponente,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
    TipoOrigemComponente,
)
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8

# ============================================================
# T-CAL-119 — analisar_correlacao_componentes
# ============================================================


def _comp(
    *,
    orc_id: UUID,
    tenant_id: UUID,
    fonte_padrao: UUID | None = None,
    correlacao_com: UUID | None = None,
    comp_id: UUID | None = None,
) -> ComponenteIncertezaSnapshot:
    return ComponenteIncertezaSnapshot(
        id=comp_id or uuid4(),
        tenant_id=tenant_id,
        orcamento_incerteza_id=orc_id,
        nome_componente="X",
        tipo_componente="B",
        tipo_origem_componente=TipoOrigemComponente.OUTRO,
        distribuicao=DistribuicaoIncerteza.RETANGULAR,
        divisor=Decimal("1.73205"),
        formula_calculo=FormulaCalculoComponente.OUTRO,
        valor_estimativa=Decimal("0.1"),
        contribuicao=Decimal("0.01"),
        grau_liberdade=None,
        n_amostras=None,
        s_x=None,
        correlacao_com_componente_id=correlacao_com,
        coeficiente_correlacao=Decimal("0.5") if correlacao_com else None,
        fonte_default_padrao_id=fonte_padrao,
    )


class TestAnalisarCorrelacaoComponentes:
    def test_sem_fonte_compartilhada_nao_alerta(self) -> None:
        orc, tenant = uuid4(), uuid4()
        comps = [
            _comp(orc_id=orc, tenant_id=tenant, fonte_padrao=uuid4()),
            _comp(orc_id=orc, tenant_id=tenant, fonte_padrao=uuid4()),
        ]
        alertas = analisar_correl_executar(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=comps,
        )
        assert alertas == []

    def test_fonte_compartilhada_sem_correlacao_alerta(self) -> None:
        orc, tenant, padrao = uuid4(), uuid4(), uuid4()
        comps = [
            _comp(orc_id=orc, tenant_id=tenant, fonte_padrao=padrao),
            _comp(orc_id=orc, tenant_id=tenant, fonte_padrao=padrao),
        ]
        alertas = analisar_correl_executar(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=comps,
        )
        assert len(alertas) == 1
        assert alertas[0].fonte_default_padrao_id == padrao
        assert len(alertas[0].componentes_envolvidos_ids) == 2

    def test_fonte_compartilhada_com_correlacao_intra_grupo_passa(self) -> None:
        orc, tenant, padrao = uuid4(), uuid4(), uuid4()
        comp_a_id = uuid4()
        comp_b_id = uuid4()
        comps = [
            _comp(
                orc_id=orc,
                tenant_id=tenant,
                fonte_padrao=padrao,
                comp_id=comp_a_id,
                correlacao_com=comp_b_id,
            ),
            _comp(
                orc_id=orc,
                tenant_id=tenant,
                fonte_padrao=padrao,
                comp_id=comp_b_id,
                correlacao_com=comp_a_id,
            ),
        ]
        alertas = analisar_correl_executar(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=comps,
        )
        assert alertas == []

    def test_correlacao_com_componente_de_outro_grupo_alerta(self) -> None:
        orc, tenant = uuid4(), uuid4()
        padrao_a = uuid4()
        comp_externo_id = uuid4()  # outro grupo
        comps = [
            _comp(
                orc_id=orc,
                tenant_id=tenant,
                fonte_padrao=padrao_a,
                correlacao_com=comp_externo_id,
            ),
            _comp(
                orc_id=orc,
                tenant_id=tenant,
                fonte_padrao=padrao_a,
                correlacao_com=comp_externo_id,
            ),
        ]
        alertas = analisar_correl_executar(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=comps,
        )
        assert len(alertas) == 1

    def test_fonte_none_ignora(self) -> None:
        orc, tenant = uuid4(), uuid4()
        comps = [
            _comp(orc_id=orc, tenant_id=tenant, fonte_padrao=None),
            _comp(orc_id=orc, tenant_id=tenant, fonte_padrao=None),
        ]
        alertas = analisar_correl_executar(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=comps,
        )
        assert alertas == []

    def test_filtra_tenant_diferente(self) -> None:
        orc = uuid4()
        tenant_a, tenant_b = uuid4(), uuid4()
        padrao = uuid4()
        comps = [
            _comp(orc_id=orc, tenant_id=tenant_a, fonte_padrao=padrao),
            _comp(orc_id=orc, tenant_id=tenant_b, fonte_padrao=padrao),
        ]
        alertas = analisar_correl_executar(
            orcamento_incerteza_id=orc,
            tenant_id=tenant_a,
            correlation_id=uuid4(),
            componentes=comps,
        )
        # So 1 do tenant_a -> nao tem grupo de 2 -> sem alerta
        assert alertas == []

    def test_filtra_orcamento_diferente(self) -> None:
        orc_a, orc_b = uuid4(), uuid4()
        tenant, padrao = uuid4(), uuid4()
        comps = [
            _comp(orc_id=orc_a, tenant_id=tenant, fonte_padrao=padrao),
            _comp(orc_id=orc_b, tenant_id=tenant, fonte_padrao=padrao),
        ]
        alertas = analisar_correl_executar(
            orcamento_incerteza_id=orc_a,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=comps,
        )
        assert alertas == []  # so 1 do orc_a

    def test_alerta_preserva_correlation_id(self) -> None:
        orc, tenant, padrao = uuid4(), uuid4(), uuid4()
        cid = uuid4()
        comps = [
            _comp(orc_id=orc, tenant_id=tenant, fonte_padrao=padrao),
            _comp(orc_id=orc, tenant_id=tenant, fonte_padrao=padrao),
        ]
        alertas = analisar_correl_executar(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=cid,
            componentes=comps,
        )
        assert alertas[0].correlation_id == cid


# ============================================================
# T-CAL-120 — geo_truncamento_calibracao_5a
# ============================================================


def _cal_aprovada(
    *,
    criada_em: datetime,
    snapshot_geo: dict[str, object] | None = None,
    tenant_id: UUID | None = None,
) -> CalibracaoSnapshot:
    return CalibracaoSnapshot(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        numero_interno=1,
        numero_exibido="",
        origem_recepcao=OrigemRecepcao.AVULSA,
        atividade_os_id=None,
        instrumento_id=uuid4(),
        snapshot_equipamento_json=snapshot_geo or {"nome": "balanca"},
        cliente_id=None,
        cliente_referencia_hash="v01$c",
        cliente_key_id="k",
        tipo_acreditacao=TipoAcreditacao.NAO_RBC,
        status=EstadoCalibracao.APROVADA,
        revision=5,
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
        zona_ilac_g8=ZonaILACG8.PASS,
        decisao="CONFORME",
        pfa_calculada=None,
        pra_calculada=None,
        subcontratado_id=None,
        aceite_subcontratacao_id=None,
        certificado_subcontratado_snapshot_json=None,
        recebedor_user_id=None,
        correlation_id=uuid4(),
        causation_id=None,
        criada_em=criada_em,
        criada_por_user_id=None,
    )


class TestGeoTruncamento5a:
    AGORA = datetime(2030, 6, 30, 12, 0, tzinfo=UTC)

    def test_recente_nao_trunca(self) -> None:
        cal = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 2),
            snapshot_geo={"latitude": -23.5, "longitude": -46.6, "nome": "bal"},
        )
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[cal], agora=self.AGORA
        )
        assert acoes == []

    def test_alem_5a_com_geo_trunca(self) -> None:
        cal = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 6),
            snapshot_geo={
                "latitude": -23.5,
                "longitude": -46.6,
                "nome": "bal",
            },
        )
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[cal], agora=self.AGORA
        )
        assert len(acoes) == 1
        assert "latitude" in acoes[0].chaves_removidas
        assert "longitude" in acoes[0].chaves_removidas
        assert "nome" in acoes[0].snapshot_equipamento_json_novo
        assert "latitude" not in acoes[0].snapshot_equipamento_json_novo

    def test_alem_5a_sem_geo_nao_trunca(self) -> None:
        cal = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 6),
            snapshot_geo={"nome": "bal", "modelo": "X-100", "num_serie": "ABC"},
        )
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[cal], agora=self.AGORA
        )
        assert acoes == []

    def test_remove_lat_long_cep_endereco_complemento(self) -> None:
        cal = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 10),
            snapshot_geo={
                "lat": -23.5,
                "long": -46.6,
                "lng": -46.6,
                "cep": "01234-567",
                "endereco_completo": "Rua X, 123",
                "complemento": "ap 1",
                "nome": "bal",
                "modelo": "X-100",
            },
        )
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[cal], agora=self.AGORA
        )
        assert len(acoes) == 1
        removidas = set(acoes[0].chaves_removidas)
        assert removidas == {
            "lat",
            "long",
            "lng",
            "cep",
            "endereco_completo",
            "complemento",
        }
        assert set(acoes[0].snapshot_equipamento_json_novo.keys()) == {
            "nome",
            "modelo",
        }

    def test_status_em_revisao_ignora(self) -> None:
        cal = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 6),
            snapshot_geo={"latitude": -23.5},
        )
        from dataclasses import replace as _r

        cal_revisao = _r(cal, status=EstadoCalibracao.EM_REVISAO_1)
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[cal_revisao], agora=self.AGORA
        )
        assert acoes == []

    def test_borda_5a_exato_nao_trunca(self) -> None:
        """Exatos 5 anos (365*5 dias) — corte = agora - 5a; criada_em == corte;
        condicao `criada_em > corte` False -> elegivel."""
        cal = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 5),
            snapshot_geo={"latitude": -23.5},
        )
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[cal], agora=self.AGORA
        )
        # criada_em == corte -> elegivel
        assert len(acoes) == 1

    def test_4a_exato_nao_trunca(self) -> None:
        cal = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 4),
            snapshot_geo={"latitude": -23.5},
        )
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[cal], agora=self.AGORA
        )
        assert acoes == []

    def test_agora_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            geo_trunc_executar(
                calibracoes_aprovadas=[],
                agora=datetime(2026, 6, 30, 12, 0),
            )

    def test_multiplas_so_elegiveis(self) -> None:
        cal_recente = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 2),
            snapshot_geo={"latitude": -23.5},
        )
        cal_velha_com_geo = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 6),
            snapshot_geo={"latitude": -23.5, "nome": "bal"},
        )
        cal_velha_sem_geo = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 8),
            snapshot_geo={"nome": "bal"},
        )
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[
                cal_recente,
                cal_velha_com_geo,
                cal_velha_sem_geo,
            ],
            agora=self.AGORA,
        )
        assert len(acoes) == 1
        assert acoes[0].calibracao_id == cal_velha_com_geo.id

    def test_case_insensitive_chave(self) -> None:
        cal = _cal_aprovada(
            criada_em=self.AGORA - timedelta(days=365 * 6),
            snapshot_geo={"LATITUDE": -23.5, "Longitude": -46.6, "nome": "bal"},
        )
        acoes = geo_trunc_executar(
            calibracoes_aprovadas=[cal], agora=self.AGORA
        )
        assert len(acoes) == 1
        assert "LATITUDE" in acoes[0].chaves_removidas
        assert "Longitude" in acoes[0].chaves_removidas
