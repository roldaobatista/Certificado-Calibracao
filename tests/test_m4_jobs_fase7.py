"""Tests M4 P4 Fase 7 — 3 jobs puros (Batch Q).

T-CAL-116 alertar_reclamacao_vencendo (AC-CAL-018-3).
T-CAL-117 pseudonimizar_responsavel_nc (P-CAL-A2).
T-CAL-121 analisar_uso_excecao_2a_conferencia (AC-CAL-008-5 + P-CAL-S9).

Jobs sao funcoes PURAS — testaveis sem DB.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.jobs.alertar_reclamacao_vencendo import (
    executar as alertar_reclamacao_executar,
)
from src.application.metrologia.calibracao.jobs.analisar_uso_excecao_2a_conferencia import (
    executar as analisar_excecao_executar,
)
from src.application.metrologia.calibracao.jobs.pseudonimizar_responsavel_nc import (
    executar as pseudonimizar_executar,
)
from src.domain.metrologia.calibracao.entities import (
    CalibracaoSnapshot,
    NaoConformidadeSnapshot,
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

# ============================================================
# Builders mínimos
# ============================================================


def _reclamacao(
    *,
    estado: EstadoReclamacao = EstadoReclamacao.EM_ANALISE,
    aberta_em: datetime,
    prazo_dia_util: int = 15,
    tenant_id: UUID | None = None,
) -> ReclamacaoCalibracaoSnapshot:
    return ReclamacaoCalibracaoSnapshot(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        calibracao_id=uuid4(),
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
    *,
    estado: EstadoNaoConformidade = EstadoNaoConformidade.ACAO_EXECUTADA,
    acao_executada_em: datetime | None,
    responsavel_user_id: UUID | None = None,
    responsavel_hash: str = "v01$resp",
) -> NaoConformidadeSnapshot:
    return NaoConformidadeSnapshot(
        id=uuid4(),
        tenant_id=uuid4(),
        calibracao_id=uuid4(),
        origem_proficiencia_id=None,
        descricao_canonicalizada="d" * 60,
        descricao_hash="v01$d",
        estado=estado,
        causa_raiz_canonicalizada="c" * 60,
        causa_raiz_hash="v01$c",
        acao_corretiva_descricao_hash="v01$a",
        acao_corretiva_tipo=None,
        acao_executada_em=acao_executada_em,
        eficacia_verificada_em=None,
        eficacia_verificada_por_user_id=None,
        responsavel_acao_user_id=responsavel_user_id or uuid4(),
        responsavel_acao_user_id_hash=responsavel_hash,
        decisao_continuar_ou_parar=DecisaoContinuarOuParar.CONTINUAR_COM_CONTROLE,
        cliente_notificado_em=None,
        cliente_notificado_via=None,
        cliente_notificado_documento_id=None,
        autorizacao_retomada_user_id=None,
        autorizacao_retomada_em=None,
        correlation_id=uuid4(),
    )


def _calibracao_aprovada(
    *,
    tenant_id: UUID,
    criada_em: datetime,
    com_excecao: bool = False,
) -> CalibracaoSnapshot:
    return CalibracaoSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
        numero_interno=1,
        numero_exibido="",
        origem_recepcao=OrigemRecepcao.AVULSA,
        atividade_os_id=None,
        instrumento_id=uuid4(),
        snapshot_equipamento_json={},
        cliente_id=uuid4(),
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
        executor_id=uuid4(),
        revisor_id=uuid4(),
        conferente_id=uuid4(),
        snapshot_competencia_revisor_json=None,
        snapshot_competencia_conferente_json=None,
        excecao_2a_conf_id=uuid4() if com_excecao else None,
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


# ============================================================
# T-CAL-116 — alertar_reclamacao_vencendo
# ============================================================


class TestAlertarReclamacaoVencendo:
    AGORA = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)

    def test_dentro_prazo_nao_alerta(self) -> None:
        # 15 d.u. ≈ 21 dias corridos. Aberta ha 10 dias -> dentro do prazo.
        recl = _reclamacao(aberta_em=self.AGORA - timedelta(days=10))
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[recl], agora=self.AGORA
        )
        assert alertas == []

    def test_prazo_estourado_alerta(self) -> None:
        # Aberta ha 30 dias -> bem alem dos 21 dias corridos (15 d.u.)
        recl = _reclamacao(aberta_em=self.AGORA - timedelta(days=30))
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[recl], agora=self.AGORA
        )
        assert len(alertas) == 1
        assert alertas[0].reclamacao_id == recl.id
        assert alertas[0].dias_atrasada >= 1

    def test_borda_exata_21_dias_nao_alerta(self) -> None:
        recl = _reclamacao(aberta_em=self.AGORA - timedelta(days=21))
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[recl], agora=self.AGORA
        )
        # 21 dias = limite exato (15 * 1.40 = 21) — nao estoura
        assert alertas == []

    def test_22_dias_estoura(self) -> None:
        recl = _reclamacao(
            aberta_em=self.AGORA - timedelta(days=22, hours=1)
        )
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[recl], agora=self.AGORA
        )
        assert len(alertas) == 1

    def test_estado_respondida_ignora(self) -> None:
        recl = _reclamacao(
            estado=EstadoReclamacao.RESPONDIDA,
            aberta_em=self.AGORA - timedelta(days=30),
        )
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[recl], agora=self.AGORA
        )
        assert alertas == []

    def test_recebida_tambem_alerta(self) -> None:
        recl = _reclamacao(
            estado=EstadoReclamacao.RECEBIDA,
            aberta_em=self.AGORA - timedelta(days=30),
        )
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[recl], agora=self.AGORA
        )
        assert len(alertas) == 1
        assert alertas[0].estado_atual == EstadoReclamacao.RECEBIDA

    def test_multiplas_so_estouradas(self) -> None:
        r_ok = _reclamacao(aberta_em=self.AGORA - timedelta(days=5))
        r_estourada = _reclamacao(aberta_em=self.AGORA - timedelta(days=30))
        r_estourada2 = _reclamacao(aberta_em=self.AGORA - timedelta(days=40))
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[r_ok, r_estourada, r_estourada2],
            agora=self.AGORA,
        )
        ids = {a.reclamacao_id for a in alertas}
        assert ids == {r_estourada.id, r_estourada2.id}

    def test_agora_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            alertar_reclamacao_executar(
                reclamacoes_abertas=[],
                agora=datetime(2026, 6, 30, 12, 0),
            )

    def test_prazo_customizado_30d_util(self) -> None:
        # 30 d.u. ≈ 42 dias corridos.
        recl = _reclamacao(
            aberta_em=self.AGORA - timedelta(days=35),
            prazo_dia_util=30,
        )
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[recl], agora=self.AGORA
        )
        assert alertas == []  # 35 < 42

        recl_estouro = _reclamacao(
            aberta_em=self.AGORA - timedelta(days=50),
            prazo_dia_util=30,
        )
        alertas = alertar_reclamacao_executar(
            reclamacoes_abertas=[recl_estouro], agora=self.AGORA
        )
        assert len(alertas) == 1


# ============================================================
# T-CAL-117 — pseudonimizar_responsavel_nc
# ============================================================


class TestPseudonimizarResponsavelNC:
    AGORA = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)

    def test_acao_recente_nao_pseudonimiza(self) -> None:
        # Acao executada ha 30 dias < 90d
        nc = _nc(acao_executada_em=self.AGORA - timedelta(days=30))
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert acoes == []

    def test_acao_alem_90d_pseudonimiza(self) -> None:
        nc = _nc(acao_executada_em=self.AGORA - timedelta(days=95))
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert len(acoes) == 1
        assert acoes[0].nc_id == nc.id
        assert acoes[0].dias_desde_execucao >= 90

    def test_borda_exata_90d_pseudonimiza(self) -> None:
        # Em 90 dias exatos, corte == acao_executada_em -> nao pseudonimiza
        # (estritamente menor que corte). Em 91d -> pseudonimiza.
        nc_90 = _nc(acao_executada_em=self.AGORA - timedelta(days=90))
        acoes_90 = pseudonimizar_executar(
            ncs_com_responsavel=[nc_90], agora=self.AGORA
        )
        # Corte = agora - 90d; acao_executada_em == corte; condicao
        # `acao_executada_em > corte` eh False -> elegivel.
        assert len(acoes_90) == 1

    def test_fechada_pseudonimiza(self) -> None:
        nc = _nc(
            estado=EstadoNaoConformidade.FECHADA,
            acao_executada_em=self.AGORA - timedelta(days=120),
        )
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert len(acoes) == 1

    def test_eficacia_verificada_pseudonimiza(self) -> None:
        nc = _nc(
            estado=EstadoNaoConformidade.EFICACIA_VERIFICADA,
            acao_executada_em=self.AGORA - timedelta(days=120),
        )
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert len(acoes) == 1

    def test_contida_nao_pseudonimiza_mesmo_com_responsavel(self) -> None:
        nc = _nc(
            estado=EstadoNaoConformidade.CONTIDA,
            acao_executada_em=None,
        )
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert acoes == []

    def test_acao_corretiva_definida_nao_pseudonimiza(self) -> None:
        nc = _nc(
            estado=EstadoNaoConformidade.ACAO_CORRETIVA_DEFINIDA,
            acao_executada_em=None,
        )
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert acoes == []

    def test_acao_executada_em_none_nao_pseudonimiza(self) -> None:
        nc = _nc(
            estado=EstadoNaoConformidade.ACAO_EXECUTADA,
            acao_executada_em=None,  # bug, mas defesa
        )
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert acoes == []

    def test_responsavel_uuid_none_ignora(self) -> None:
        # Snapshot ja pseudonimizado anteriormente (UUID=None)
        nc = _nc(
            acao_executada_em=self.AGORA - timedelta(days=120),
            responsavel_user_id=uuid4(),
        )
        nc_sem_uuid = replace(nc, responsavel_acao_user_id=None)
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc_sem_uuid], agora=self.AGORA
        )
        assert acoes == []

    def test_hash_vazio_nao_pseudonimiza(self) -> None:
        # P-CAL-A2 — defesa: se hash nao foi gravado, nao podemos perder
        # rastro do responsavel
        nc = _nc(
            acao_executada_em=self.AGORA - timedelta(days=120),
            responsavel_hash="",
        )
        acoes = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert acoes == []

    def test_agora_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            pseudonimizar_executar(
                ncs_com_responsavel=[], agora=datetime(2026, 6, 30, 12, 0)
            )

    def test_idempotencia_chamadas_multiplas(self) -> None:
        """Apos pseudonimizar (caller faz UPDATE), proxima chamada nao
        retorna o mesmo registro (responsavel_acao_user_id passa a None)."""
        nc = _nc(acao_executada_em=self.AGORA - timedelta(days=120))
        acoes_1 = pseudonimizar_executar(
            ncs_com_responsavel=[nc], agora=self.AGORA
        )
        assert len(acoes_1) == 1
        # Simula UPDATE pelo caller
        nc_pos = replace(nc, responsavel_acao_user_id=None)
        acoes_2 = pseudonimizar_executar(
            ncs_com_responsavel=[nc_pos], agora=self.AGORA
        )
        assert acoes_2 == []


# ============================================================
# T-CAL-121 — analisar_uso_excecao_2a_conferencia
# ============================================================


class TestAnalisarUsoExcecao2aConferencia:
    AGORA = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)

    def test_zero_aprovadas_severidade_none(self) -> None:
        tenant = uuid4()
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=[],
            agora=self.AGORA,
        )
        assert out.severidade == "NONE"
        assert out.percentual == Decimal("0.0000")
        assert out.total_aprovadas == 0

    def test_uso_baixo_severidade_none(self) -> None:
        tenant = uuid4()
        cal_ok = _calibracao_aprovada(
            tenant_id=tenant,
            criada_em=self.AGORA - timedelta(days=10),
            com_excecao=False,
        )
        cals = [
            replace(cal_ok, id=uuid4(), excecao_2a_conf_id=None)
            for _ in range(100)
        ]
        # 1 com excecao em 100 = 1% < 3%
        cals[0] = replace(cals[0], excecao_2a_conf_id=uuid4())
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=cals,
            agora=self.AGORA,
        )
        assert out.severidade == "NONE"
        assert out.percentual == Decimal("0.0100")
        assert out.total_aprovadas == 100
        assert out.total_com_excecao == 1

    def test_3pct_alerta_p2(self) -> None:
        tenant = uuid4()
        base = _calibracao_aprovada(
            tenant_id=tenant,
            criada_em=self.AGORA - timedelta(days=10),
        )
        cals = [replace(base, id=uuid4(), excecao_2a_conf_id=None) for _ in range(97)]
        cals += [
            replace(base, id=uuid4(), excecao_2a_conf_id=uuid4())
            for _ in range(3)
        ]
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=cals,
            agora=self.AGORA,
        )
        assert out.severidade == "P2_ALERTA"
        assert out.percentual == Decimal("0.0300")

    def test_5pct_alerta_p1_estouro(self) -> None:
        tenant = uuid4()
        base = _calibracao_aprovada(
            tenant_id=tenant,
            criada_em=self.AGORA - timedelta(days=10),
        )
        cals = [replace(base, id=uuid4(), excecao_2a_conf_id=None) for _ in range(95)]
        cals += [
            replace(base, id=uuid4(), excecao_2a_conf_id=uuid4())
            for _ in range(5)
        ]
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=cals,
            agora=self.AGORA,
        )
        assert out.severidade == "P1_ESTOURO"
        assert out.percentual == Decimal("0.0500")

    def test_acima_5pct_estouro(self) -> None:
        tenant = uuid4()
        base = _calibracao_aprovada(
            tenant_id=tenant,
            criada_em=self.AGORA - timedelta(days=10),
        )
        cals = [replace(base, id=uuid4(), excecao_2a_conf_id=None) for _ in range(90)]
        cals += [
            replace(base, id=uuid4(), excecao_2a_conf_id=uuid4())
            for _ in range(10)
        ]
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=cals,
            agora=self.AGORA,
        )
        assert out.severidade == "P1_ESTOURO"
        assert out.percentual == Decimal("0.1000")

    def test_fora_janela_30d_ignora(self) -> None:
        tenant = uuid4()
        # Tudo fora dos 30d (criada ha 45d) -> ignora
        antiga = _calibracao_aprovada(
            tenant_id=tenant,
            criada_em=self.AGORA - timedelta(days=45),
            com_excecao=True,
        )
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=[antiga],
            agora=self.AGORA,
        )
        assert out.total_aprovadas == 0

    def test_tenant_errado_ignora(self) -> None:
        tenant = uuid4()
        outro_tenant = uuid4()
        cal_outro = _calibracao_aprovada(
            tenant_id=outro_tenant,
            criada_em=self.AGORA - timedelta(days=10),
            com_excecao=True,
        )
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=[cal_outro],
            agora=self.AGORA,
        )
        assert out.total_aprovadas == 0

    def test_status_nao_aprovada_ignora(self) -> None:
        tenant = uuid4()
        cal = _calibracao_aprovada(
            tenant_id=tenant,
            criada_em=self.AGORA - timedelta(days=10),
        )
        cal_em_revisao = replace(cal, status=EstadoCalibracao.EM_REVISAO_1)
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=[cal_em_revisao],
            agora=self.AGORA,
        )
        assert out.total_aprovadas == 0

    def test_agora_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            analisar_excecao_executar(
                tenant_id=uuid4(),
                calibracoes_aprovadas_janela=[],
                agora=datetime(2026, 6, 30, 12, 0),
            )

    def test_metadata_janela_correto(self) -> None:
        tenant = uuid4()
        out = analisar_excecao_executar(
            tenant_id=tenant,
            calibracoes_aprovadas_janela=[],
            agora=self.AGORA,
        )
        assert out.tenant_id == tenant
        assert out.janela_fim == self.AGORA
        assert out.janela_inicio == self.AGORA - timedelta(days=30)
