"""Tests Fase 6 M4 — 3 query services puros.

- visao_360 (T-CAL-106)
- reclamacoes_abertas (T-CAL-112)
- fila_revisor_conferente
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.queries.fila_revisor_conferente import (
    fila_conferente,
    fila_revisor,
)
from src.application.metrologia.calibracao.queries.reclamacoes_abertas import (
    executar as reclamacoes_abertas_executar,
)
from src.application.metrologia.calibracao.queries.visao_360 import (
    executar as visao_360_executar,
)
from src.domain.metrologia.calibracao.entities import (
    CalibracaoSnapshot,
    LeituraSnapshot,
    NaoConformidadeSnapshot,
    OrigemLeitura,
    ReclamacaoCalibracaoSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    DecisaoContinuarOuParar,
    EstadoCalibracao,
    EstadoNaoConformidade,
    EstadoReclamacao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8

AGORA = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


# ============================================================
# Builders
# ============================================================


def _cal(
    *,
    tenant_id: UUID | None = None,
    cal_id: UUID | None = None,
    status: EstadoCalibracao = EstadoCalibracao.EM_REVISAO_1,
    criada_em: datetime | None = None,
    executor_id: UUID | None = None,
    revisor_id: UUID | None = None,
) -> CalibracaoSnapshot:
    return CalibracaoSnapshot(
        id=cal_id or uuid4(),
        tenant_id=tenant_id or uuid4(),
        numero_interno=1,
        numero_exibido="CAL-2026-000001",
        origem_recepcao=OrigemRecepcao.AVULSA,
        atividade_os_id=None,
        instrumento_id=uuid4(),
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
        executor_id=executor_id,
        revisor_id=revisor_id,
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


def _leitura(*, tenant_id: UUID, cal_id: UUID, ts: datetime) -> LeituraSnapshot:
    return LeituraSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
        calibracao_id=cal_id,
        ponto_calibracao=Decimal("10"),
        numero_repeticao=1,
        valor_lido=Decimal("10.1"),
        unidade="kg",
        origem=OrigemLeitura.MANUAL,
        timestamp=ts,
        executor_id_hash="v01$exec",
        client_event_id=None,
        correlation_id=uuid4(),
    )


def _reclamacao(
    *,
    tenant_id: UUID,
    cal_id: UUID,
    aberta_em: datetime,
    estado: EstadoReclamacao = EstadoReclamacao.EM_ANALISE,
    prazo_dia_util: int = 15,
) -> ReclamacaoCalibracaoSnapshot:
    return ReclamacaoCalibracaoSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
        calibracao_id=cal_id,
        certificado_id=uuid4(),
        cliente_referencia_hash="v01$c",
        relato_canonicalizado="x" * 120,
        relato_hash="v01$x",
        estado=estado,
        rt_atribuido_user_id_hash="v01$rt",
        resposta_canonicalizada="",
        resposta_hash="",
        decisao=None,
        aberta_em=aberta_em,
        prazo_resposta_dia_util=prazo_dia_util,
        respondida_em=None,
        correlation_id=uuid4(),
    )


def _nc(
    *, tenant_id: UUID, cal_id: UUID, estado: EstadoNaoConformidade
) -> NaoConformidadeSnapshot:
    return NaoConformidadeSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
        calibracao_id=cal_id,
        origem_proficiencia_id=None,
        descricao_canonicalizada="d" * 60,
        descricao_hash="v01$d",
        estado=estado,
        causa_raiz_canonicalizada="",
        causa_raiz_hash="",
        acao_corretiva_descricao_hash="",
        acao_corretiva_tipo=None,
        acao_executada_em=None,
        eficacia_verificada_em=None,
        eficacia_verificada_por_user_id=None,
        responsavel_acao_user_id=uuid4(),
        responsavel_acao_user_id_hash="v01$resp",
        decisao_continuar_ou_parar=DecisaoContinuarOuParar.A_DEFINIR,
        cliente_notificado_em=None,
        cliente_notificado_via=None,
        cliente_notificado_documento_id=None,
        autorizacao_retomada_user_id=None,
        autorizacao_retomada_em=None,
        correlation_id=uuid4(),
    )


# ============================================================
# T-CAL-106 — visao_360
# ============================================================


class TestVisao360:
    def test_agrega_calibracao_sozinha(self) -> None:
        cal = _cal()
        v = visao_360_executar(
            calibracao_id=cal.id,
            calibracao=cal,
            leituras=[],
            orcamento=None,
            componentes_orcamento=[],
            nao_conformidades=[],
            reclamacoes=[],
        )
        assert v.calibracao == cal
        assert v.total_leituras == 0
        assert not v.tem_nc_aberta
        assert not v.tem_reclamacao_aberta

    def test_leituras_ordem_cronologica(self) -> None:
        tenant = uuid4()
        cal = _cal(tenant_id=tenant)
        lt2 = _leitura(tenant_id=tenant, cal_id=cal.id, ts=AGORA)
        lt1 = _leitura(
            tenant_id=tenant, cal_id=cal.id, ts=AGORA - timedelta(hours=1)
        )
        v = visao_360_executar(
            calibracao_id=cal.id,
            calibracao=cal,
            leituras=[lt2, lt1],  # ordem invertida na entrada
            orcamento=None,
            componentes_orcamento=[],
            nao_conformidades=[],
            reclamacoes=[],
        )
        assert v.leituras[0].id == lt1.id  # mais antiga primeiro
        assert v.leituras[1].id == lt2.id

    def test_filtra_leituras_tenant_errado(self) -> None:
        cal = _cal()
        outro_tenant = uuid4()
        lt_outra = _leitura(tenant_id=outro_tenant, cal_id=cal.id, ts=AGORA)
        v = visao_360_executar(
            calibracao_id=cal.id,
            calibracao=cal,
            leituras=[lt_outra],
            orcamento=None,
            componentes_orcamento=[],
            nao_conformidades=[],
            reclamacoes=[],
        )
        assert v.leituras == ()

    def test_filtra_leituras_outra_calibracao(self) -> None:
        cal = _cal()
        lt_outra_cal = _leitura(tenant_id=cal.tenant_id, cal_id=uuid4(), ts=AGORA)
        v = visao_360_executar(
            calibracao_id=cal.id,
            calibracao=cal,
            leituras=[lt_outra_cal],
            orcamento=None,
            componentes_orcamento=[],
            nao_conformidades=[],
            reclamacoes=[],
        )
        assert v.leituras == ()

    def test_calibracao_id_mismatch_recusa(self) -> None:
        cal = _cal()
        with pytest.raises(ValueError, match="calibracao_id"):
            visao_360_executar(
                calibracao_id=uuid4(),
                calibracao=cal,
                leituras=[],
                orcamento=None,
                componentes_orcamento=[],
                nao_conformidades=[],
                reclamacoes=[],
            )

    def test_tem_nc_aberta_flag(self) -> None:
        cal = _cal()
        nc_aberta = _nc(
            tenant_id=cal.tenant_id,
            cal_id=cal.id,
            estado=EstadoNaoConformidade.CONTIDA,
        )
        nc_fechada = _nc(
            tenant_id=cal.tenant_id,
            cal_id=cal.id,
            estado=EstadoNaoConformidade.FECHADA,
        )
        v = visao_360_executar(
            calibracao_id=cal.id,
            calibracao=cal,
            leituras=[],
            orcamento=None,
            componentes_orcamento=[],
            nao_conformidades=[nc_aberta, nc_fechada],
            reclamacoes=[],
        )
        assert v.tem_nc_aberta is True
        assert len(v.nao_conformidades) == 2

    def test_so_nc_fechada_nao_tem_aberta(self) -> None:
        cal = _cal()
        nc_fechada = _nc(
            tenant_id=cal.tenant_id,
            cal_id=cal.id,
            estado=EstadoNaoConformidade.FECHADA,
        )
        v = visao_360_executar(
            calibracao_id=cal.id,
            calibracao=cal,
            leituras=[],
            orcamento=None,
            componentes_orcamento=[],
            nao_conformidades=[nc_fechada],
            reclamacoes=[],
        )
        assert v.tem_nc_aberta is False

    def test_tem_reclamacao_aberta_flag(self) -> None:
        cal = _cal()
        recl = _reclamacao(
            tenant_id=cal.tenant_id,
            cal_id=cal.id,
            aberta_em=AGORA - timedelta(days=1),
            estado=EstadoReclamacao.EM_ANALISE,
        )
        v = visao_360_executar(
            calibracao_id=cal.id,
            calibracao=cal,
            leituras=[],
            orcamento=None,
            componentes_orcamento=[],
            nao_conformidades=[],
            reclamacoes=[recl],
        )
        assert v.tem_reclamacao_aberta is True


# ============================================================
# T-CAL-112 — reclamacoes_abertas
# ============================================================


class TestReclamacoesAbertas:
    def test_vazio_retorna_lista_vazia(self) -> None:
        assert (
            reclamacoes_abertas_executar(reclamacoes=[], agora=AGORA) == []
        )

    def test_ordena_vencidas_primeiro(self) -> None:
        tenant = uuid4()
        cal_id = uuid4()
        r_recente = _reclamacao(
            tenant_id=tenant, cal_id=cal_id, aberta_em=AGORA - timedelta(days=1)
        )
        r_vencida = _reclamacao(
            tenant_id=tenant, cal_id=cal_id, aberta_em=AGORA - timedelta(days=30)
        )
        r_proxima = _reclamacao(
            tenant_id=tenant, cal_id=cal_id, aberta_em=AGORA - timedelta(days=18)
        )
        itens = reclamacoes_abertas_executar(
            reclamacoes=[r_recente, r_vencida, r_proxima], agora=AGORA
        )
        assert len(itens) == 3
        # mais urgente primeiro
        assert itens[0].reclamacao_id == r_vencida.id
        assert itens[0].urgencia == "P1_VENCIDA"

    def test_filtra_terminais(self) -> None:
        tenant = uuid4()
        r_respondida = _reclamacao(
            tenant_id=tenant,
            cal_id=uuid4(),
            aberta_em=AGORA - timedelta(days=10),
            estado=EstadoReclamacao.RESPONDIDA,
        )
        itens = reclamacoes_abertas_executar(
            reclamacoes=[r_respondida], agora=AGORA
        )
        assert itens == []

    def test_urgencia_p2_proximo_5d(self) -> None:
        tenant = uuid4()
        # 19 dias atras: dentro do prazo de 21d, com 2 dias restantes -> P2
        r = _reclamacao(
            tenant_id=tenant,
            cal_id=uuid4(),
            aberta_em=AGORA - timedelta(days=19),
        )
        itens = reclamacoes_abertas_executar(reclamacoes=[r], agora=AGORA)
        assert len(itens) == 1
        assert itens[0].urgencia == "P2_PROXIMO"

    def test_urgencia_normal(self) -> None:
        tenant = uuid4()
        r = _reclamacao(
            tenant_id=tenant,
            cal_id=uuid4(),
            aberta_em=AGORA - timedelta(days=2),
        )
        itens = reclamacoes_abertas_executar(reclamacoes=[r], agora=AGORA)
        assert len(itens) == 1
        assert itens[0].urgencia == "NORMAL"

    def test_filtra_tenant(self) -> None:
        tenant_a = uuid4()
        tenant_b = uuid4()
        r_a = _reclamacao(
            tenant_id=tenant_a,
            cal_id=uuid4(),
            aberta_em=AGORA - timedelta(days=10),
        )
        r_b = _reclamacao(
            tenant_id=tenant_b,
            cal_id=uuid4(),
            aberta_em=AGORA - timedelta(days=10),
        )
        itens = reclamacoes_abertas_executar(
            reclamacoes=[r_a, r_b], agora=AGORA, tenant_id=tenant_a
        )
        assert len(itens) == 1
        assert itens[0].tenant_id == tenant_a

    def test_agora_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            reclamacoes_abertas_executar(
                reclamacoes=[], agora=datetime(2026, 7, 1, 12, 0)
            )


# ============================================================
# fila_revisor_conferente
# ============================================================


class TestFilaRevisorConferente:
    def test_fila_revisor_filtra_em_revisao_1(self) -> None:
        cals = [
            _cal(status=EstadoCalibracao.EM_REVISAO_1),
            _cal(status=EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA),
            _cal(status=EstadoCalibracao.APROVADA),
        ]
        itens = fila_revisor(calibracoes=cals)
        assert len(itens) == 1
        assert itens[0].calibracao_id == cals[0].id

    def test_fila_conferente_filtra_aguardando_2a(self) -> None:
        cals = [
            _cal(status=EstadoCalibracao.EM_REVISAO_1),
            _cal(status=EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA),
            _cal(status=EstadoCalibracao.APROVADA),
        ]
        itens = fila_conferente(calibracoes=cals)
        assert len(itens) == 1
        assert itens[0].calibracao_id == cals[1].id

    def test_fifo_por_criada_em(self) -> None:
        c_velha = _cal(
            status=EstadoCalibracao.EM_REVISAO_1,
            criada_em=AGORA - timedelta(days=10),
        )
        c_nova = _cal(
            status=EstadoCalibracao.EM_REVISAO_1,
            criada_em=AGORA - timedelta(days=1),
        )
        itens = fila_revisor(calibracoes=[c_nova, c_velha])
        # velha primeiro (FIFO)
        assert itens[0].calibracao_id == c_velha.id
        assert itens[1].calibracao_id == c_nova.id

    def test_filtra_tenant(self) -> None:
        tenant_a = uuid4()
        tenant_b = uuid4()
        cal_a = _cal(status=EstadoCalibracao.EM_REVISAO_1, tenant_id=tenant_a)
        cal_b = _cal(status=EstadoCalibracao.EM_REVISAO_1, tenant_id=tenant_b)
        itens = fila_revisor(calibracoes=[cal_a, cal_b], tenant_id=tenant_a)
        assert len(itens) == 1
        assert itens[0].tenant_id == tenant_a

    def test_fila_conferente_traz_revisor_id(self) -> None:
        revisor = uuid4()
        cal = _cal(
            status=EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA,
            revisor_id=revisor,
        )
        itens = fila_conferente(calibracoes=[cal])
        assert itens[0].revisor_id == revisor
