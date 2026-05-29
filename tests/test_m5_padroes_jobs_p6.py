"""Testes P6 — job puro `alertar_padroes_pendencias` (T-PAD-050).

Puros (sem Django). Cobrem os 4 tipos de pendencia + janelas de
antecedencia + caso negativo (nada a alertar) + tz-aware guard +
clamp de mes na proxima VI + origem revogada nao realerta.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.padroes.jobs import alertar_padroes_pendencias as job
from src.application.metrologia.padroes.jobs.alertar_padroes_pendencias import (
    PadraoComUltimaVI,
    TipoAlertaPadrao,
)
from src.domain.metrologia.padroes.entities import (
    PadraoMetrologicoSnapshot,
    RecalExternoPadraoSnapshot,
)
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    EstadoPadrao,
    StatusRecal,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)

TENANT = uuid4()
AGORA = datetime(2026, 6, 1, 4, 0, tzinfo=UTC)


def _padrao(
    *,
    proximo_recal: date = date(2027, 1, 1),
    intervalo_vi_meses: int = 6,
    vigencia_inicio: datetime = datetime(2026, 1, 1, tzinfo=UTC),
    estado: EstadoPadrao = EstadoPadrao.EM_USO,
    rastreabilidade_origem_revogada: bool = False,
    numero_serie: str = "PESO-E2-001",
) -> PadraoMetrologicoSnapshot:
    return PadraoMetrologicoSnapshot(
        id=uuid4(),
        tenant_id=TENANT,
        numero_serie=numero_serie,
        fabricante="Mettler",
        modelo="M-1kg",
        subtipo=SubtipoPadrao.PRINCIPAL,
        grandezas=(Grandeza.MASSA,),
        faixas=(FaixaMedicao(Decimal("0"), Decimal("1"), "kg"),),
        incertezas_certificado=(
            IncertezaExpandida(
                Decimal("0.0001"), Decimal("2"), Decimal("0.9545"), "kg"
            ),
        ),
        vinculacao=VinculacaoCadeia.INMETRO,
        classe=ClassePadrao.E2,
        cert_externo_storage_key="key-123",
        validade_certificado_rastreabilidade=date(2027, 1, 1),
        proximo_recal=proximo_recal,
        intervalo_recal_meses=12,
        intervalo_vi_meses=intervalo_vi_meses,
        criterio_intervalo="Analise de risco cl. 6.4.7.",
        estado=estado,
        revision=1,
        rastreabilidade_origem_revogada=rastreabilidade_origem_revogada,
        vigencia_inicio=vigencia_inicio,
        correlation_id=uuid4(),
    )


def _recal(
    padrao_id: UUID,
    *,
    status: StatusRecal,
    enviado_em: datetime,
    retornado_em: datetime | None = None,
    aprovado_rt_em: datetime | None = None,
) -> RecalExternoPadraoSnapshot:
    return RecalExternoPadraoSnapshot(
        id=uuid4(),
        tenant_id=TENANT,
        padrao_id=padrao_id,
        enviado_em=enviado_em,
        lab_externo="Lab RBC",
        responsavel_envio_id_hash="v1$hash",
        status=status,
        retornado_em=retornado_em,
        aprovado_rt_em=aprovado_rt_em,
    )


def _exec(**kw: Any) -> list[job.AlertaPadrao]:
    base: dict[str, Any] = {
        "padroes_em_uso": [],
        "padroes_vi": [],
        "recals_enviados": [],
        "recals_retornados": [],
        "agora": AGORA,
    }
    base.update(kw)
    return job.executar(**base)


# --------------------------------------------------------------------------
# Guard tz-aware
# --------------------------------------------------------------------------
def test_agora_naive_levanta() -> None:
    with pytest.raises(ValueError, match="tz-aware"):
        _exec(agora=datetime(2026, 6, 1, 4, 0))


def test_tudo_vazio_nao_alerta() -> None:
    assert _exec() == []


# --------------------------------------------------------------------------
# RECAL_VENCENDO
# --------------------------------------------------------------------------
class TestRecalVencendo:
    def test_dentro_janela_30d_alerta_p2(self) -> None:
        p = _padrao(proximo_recal=date(2026, 6, 20))  # 19 dias
        alertas = _exec(padroes_em_uso=[p])
        assert len(alertas) == 1
        a = alertas[0]
        assert a.tipo == TipoAlertaPadrao.RECAL_VENCENDO
        assert a.severidade == "P2_ALERTA"
        assert a.dias == 19
        assert a.padrao_id == p.id

    def test_ja_vencido_p1(self) -> None:
        p = _padrao(proximo_recal=date(2026, 5, 1))  # -31 dias
        alertas = _exec(padroes_em_uso=[p])
        assert alertas[0].severidade == "P1_VENCIDO"
        assert alertas[0].dias < 0

    def test_fora_janela_nao_alerta(self) -> None:
        p = _padrao(proximo_recal=date(2026, 12, 1))
        assert _exec(padroes_em_uso=[p]) == []

    def test_borda_exata_30d_alerta(self) -> None:
        p = _padrao(proximo_recal=date(2026, 7, 1))  # exatamente 30 dias
        assert len(_exec(padroes_em_uso=[p])) == 1

    def test_origem_revogada_nao_realerta(self) -> None:
        p = _padrao(
            proximo_recal=date(2026, 5, 1), rastreabilidade_origem_revogada=True
        )
        assert _exec(padroes_em_uso=[p]) == []


# --------------------------------------------------------------------------
# VI_PENDENTE
# --------------------------------------------------------------------------
class TestVIPendente:
    def test_ultima_vi_vencendo_alerta(self) -> None:
        p = _padrao(intervalo_vi_meses=6)
        # ultima VI em 2025-12-10 + 6 meses = 2026-06-10 -> 9 dias
        item = PadraoComUltimaVI(
            padrao=p, ultima_vi_em=datetime(2025, 12, 10, tzinfo=UTC)
        )
        alertas = _exec(padroes_vi=[item])
        assert len(alertas) == 1
        assert alertas[0].tipo == TipoAlertaPadrao.VI_PENDENTE
        assert alertas[0].dias == 9

    def test_nunca_teve_vi_usa_vigencia_inicio(self) -> None:
        # vigencia 2026-01-01 + 6 meses = 2026-07-01 -> 30 dias (borda)
        p = _padrao(
            intervalo_vi_meses=6, vigencia_inicio=datetime(2026, 1, 1, tzinfo=UTC)
        )
        item = PadraoComUltimaVI(padrao=p, ultima_vi_em=None)
        assert len(_exec(padroes_vi=[item])) == 1

    def test_vi_vencida_p1(self) -> None:
        p = _padrao(intervalo_vi_meses=3)
        item = PadraoComUltimaVI(
            padrao=p, ultima_vi_em=datetime(2026, 1, 1, tzinfo=UTC)
        )  # +3m = 2026-04-01 -> vencida ha ~61d
        assert _exec(padroes_vi=[item])[0].severidade == "P1_VI_VENCIDA"

    def test_clamp_mes_31jan_mais_1_mes(self) -> None:
        # 31/01 + 1 mes deve dar 28/02 (clamp), nao estourar
        p = _padrao(intervalo_vi_meses=1)
        item = PadraoComUltimaVI(
            padrao=p, ultima_vi_em=datetime(2026, 1, 31, tzinfo=UTC)
        )  # +1m = 2026-02-28 -> ja vencida em 01/06
        alertas = _exec(padroes_vi=[item])
        assert len(alertas) == 1

    def test_vi_distante_nao_alerta(self) -> None:
        p = _padrao(intervalo_vi_meses=12)
        item = PadraoComUltimaVI(
            padrao=p, ultima_vi_em=datetime(2026, 5, 1, tzinfo=UTC)
        )  # +12m = 2027-05-01
        assert _exec(padroes_vi=[item]) == []


# --------------------------------------------------------------------------
# RECAL_RETORNO_ATRASADO (>90d)
# --------------------------------------------------------------------------
class TestRecalRetornoAtrasado:
    def test_enviado_ha_mais_de_90d_p1(self) -> None:
        p = _padrao(estado=EstadoPadrao.EM_RECAL_EXTERNO)
        r = _recal(
            p.id,
            status=StatusRecal.ENVIADO,
            enviado_em=datetime(2026, 2, 1, tzinfo=UTC),  # ~120 dias
        )
        alertas = _exec(padroes_em_uso=[p], recals_enviados=[r])
        assert len(alertas) == 1
        a = alertas[0]
        assert a.tipo == TipoAlertaPadrao.RECAL_RETORNO_ATRASADO
        assert a.severidade == "P1_RECAL_PRESO"
        assert a.referencia_id == r.id
        assert a.dias < 0
        assert a.numero_serie == p.numero_serie

    def test_enviado_recente_nao_alerta(self) -> None:
        r = _recal(
            uuid4(),
            status=StatusRecal.ENVIADO,
            enviado_em=datetime(2026, 5, 15, tzinfo=UTC),
        )
        assert _exec(recals_enviados=[r]) == []

    def test_sem_padrao_indexado_usa_recal_id_como_correlation(self) -> None:
        rid_padrao = uuid4()
        r = _recal(
            rid_padrao,
            status=StatusRecal.ENVIADO,
            enviado_em=datetime(2026, 1, 1, tzinfo=UTC),
        )
        a = _exec(recals_enviados=[r])[0]
        assert a.correlation_id == r.id
        assert a.numero_serie == ""


# --------------------------------------------------------------------------
# RECAL_APROVACAO_RT_PENDENTE (>Nd, C-4)
# --------------------------------------------------------------------------
class TestAprovacaoRTPendente:
    def test_retornado_sem_aprovacao_apos_limite_p2(self) -> None:
        p = _padrao(estado=EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO)
        r = _recal(
            p.id,
            status=StatusRecal.RETORNADO,
            enviado_em=datetime(2026, 4, 1, tzinfo=UTC),
            retornado_em=datetime(2026, 5, 20, tzinfo=UTC),  # ~12 dias atras
        )
        alertas = _exec(padroes_em_uso=[p], recals_retornados=[r])
        assert len(alertas) == 1
        a = alertas[0]
        assert a.tipo == TipoAlertaPadrao.RECAL_APROVACAO_RT_PENDENTE
        assert a.severidade == "P2_ALERTA"
        assert a.dias < 0

    def test_ja_aprovado_nao_alerta(self) -> None:
        r = _recal(
            uuid4(),
            status=StatusRecal.RETORNADO,
            enviado_em=datetime(2026, 4, 1, tzinfo=UTC),
            retornado_em=datetime(2026, 5, 1, tzinfo=UTC),
            aprovado_rt_em=datetime(2026, 5, 2, tzinfo=UTC),
        )
        assert _exec(recals_retornados=[r]) == []

    def test_retornado_dentro_do_prazo_nao_alerta(self) -> None:
        r = _recal(
            uuid4(),
            status=StatusRecal.RETORNADO,
            enviado_em=datetime(2026, 4, 1, tzinfo=UTC),
            retornado_em=datetime(2026, 5, 30, tzinfo=UTC),  # 2 dias
        )
        assert _exec(recals_retornados=[r]) == []

    def test_limite_configuravel(self) -> None:
        r = _recal(
            uuid4(),
            status=StatusRecal.RETORNADO,
            enviado_em=datetime(2026, 4, 1, tzinfo=UTC),
            retornado_em=datetime(2026, 5, 20, tzinfo=UTC),  # ~12 dias
        )
        # com limite 30d, 12 dias nao estoura
        assert _exec(recals_retornados=[r], limite_aprovacao_rt_dias=30) == []


# --------------------------------------------------------------------------
# Consolidado: os 4 tipos numa varredura
# --------------------------------------------------------------------------
def test_consolidado_quatro_tipos() -> None:
    p_recal = _padrao(proximo_recal=date(2026, 6, 10), numero_serie="P-RECAL")
    p_vi = _padrao(numero_serie="P-VI", intervalo_vi_meses=6)
    p_preso = _padrao(
        estado=EstadoPadrao.EM_RECAL_EXTERNO, numero_serie="P-PRESO"
    )
    p_aprov = _padrao(
        estado=EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO,
        numero_serie="P-APROV",
    )
    vi_item = PadraoComUltimaVI(
        padrao=p_vi, ultima_vi_em=datetime(2025, 12, 10, tzinfo=UTC)
    )
    r_preso = _recal(
        p_preso.id,
        status=StatusRecal.ENVIADO,
        enviado_em=datetime(2026, 1, 1, tzinfo=UTC),
    )
    r_aprov = _recal(
        p_aprov.id,
        status=StatusRecal.RETORNADO,
        enviado_em=datetime(2026, 4, 1, tzinfo=UTC),
        retornado_em=datetime(2026, 5, 1, tzinfo=UTC),
    )
    alertas = _exec(
        padroes_em_uso=[p_recal, p_preso, p_aprov],
        padroes_vi=[vi_item],
        recals_enviados=[r_preso],
        recals_retornados=[r_aprov],
    )
    tipos = {a.tipo for a in alertas}
    assert tipos == {
        TipoAlertaPadrao.RECAL_VENCENDO,
        TipoAlertaPadrao.VI_PENDENTE,
        TipoAlertaPadrao.RECAL_RETORNO_ATRASADO,
        TipoAlertaPadrao.RECAL_APROVACAO_RT_PENDENTE,
    }
