"""Tests T-CAL-115 — verificar_avaliacoes_subcontratados_vencendo.

ISO 17025 cl. 6.6.2 + P-CAL-R5 + INV-CAL-SUBC-005.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.jobs.verificar_avaliacoes_subcontratados_vencendo import (
    executar,
)
from src.domain.metrologia.calibracao.entities import (
    AvaliacaoPeriodicaSubcontratadoSnapshot,
)
from src.domain.metrologia.calibracao.enums import DecisaoAvaliacaoSubcontratado


def _aval(
    *,
    proxima_avaliacao_em: datetime,
    decisao: DecisaoAvaliacaoSubcontratado = DecisaoAvaliacaoSubcontratado.MANTER,
    avaliado_em: datetime | None = None,
    laboratorio_id: UUID | None = None,
) -> AvaliacaoPeriodicaSubcontratadoSnapshot:
    return AvaliacaoPeriodicaSubcontratadoSnapshot(
        id=uuid4(),
        tenant_id=uuid4(),
        laboratorio_id=laboratorio_id or uuid4(),
        avaliado_em=avaliado_em
        or (proxima_avaliacao_em - timedelta(days=365)),
        score=Decimal("8.5"),
        decisao=decisao,
        proxima_avaliacao_em=proxima_avaliacao_em,
        correlation_id=uuid4(),
    )


AGORA = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)


class TestVerificarAvaliacoesVencendo:
    def test_normal_sem_alerta(self) -> None:
        # Proxima em 90 dias > 30 -> NONE
        aval = _aval(proxima_avaliacao_em=AGORA + timedelta(days=90))
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert alertas == []

    def test_30_dias_antes_alerta_p2(self) -> None:
        aval = _aval(proxima_avaliacao_em=AGORA + timedelta(days=15))
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert len(alertas) == 1
        assert alertas[0].severidade == "P2_ALERTA"
        assert alertas[0].dias_restantes == 15

    def test_borda_30_dias_inclusive_alerta(self) -> None:
        aval = _aval(proxima_avaliacao_em=AGORA + timedelta(days=30))
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert len(alertas) == 1
        assert alertas[0].severidade == "P2_ALERTA"

    def test_31_dias_nao_alerta(self) -> None:
        aval = _aval(proxima_avaliacao_em=AGORA + timedelta(days=31))
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert alertas == []

    def test_ja_vencida_alerta_p1(self) -> None:
        aval = _aval(proxima_avaliacao_em=AGORA - timedelta(days=5))
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert len(alertas) == 1
        assert alertas[0].severidade == "P1_VENCIDA"
        assert alertas[0].dias_restantes < 0

    def test_vencida_ha_horas_alerta_p1(self) -> None:
        """Vencida por 6h: dias_restantes deve ser -1 (qualquer atraso vira P1)."""
        aval = _aval(proxima_avaliacao_em=AGORA - timedelta(hours=6))
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert len(alertas) == 1
        assert alertas[0].severidade == "P1_VENCIDA"
        assert alertas[0].dias_restantes == -1

    def test_descredenciada_ignora(self) -> None:
        aval = _aval(
            proxima_avaliacao_em=AGORA - timedelta(days=10),
            decisao=DecisaoAvaliacaoSubcontratado.DESCREDENCIAR,
        )
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert alertas == []

    def test_acompanhamento_alerta_normalmente(self) -> None:
        aval = _aval(
            proxima_avaliacao_em=AGORA + timedelta(days=10),
            decisao=DecisaoAvaliacaoSubcontratado.ACOMPANHAMENTO,
        )
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert len(alertas) == 1
        assert alertas[0].decisao_anterior == DecisaoAvaliacaoSubcontratado.ACOMPANHAMENTO

    def test_multiplos_subcontratados_alguns_alertam(self) -> None:
        lab1 = uuid4()
        lab2 = uuid4()
        lab3 = uuid4()
        avals = [
            _aval(  # P2_ALERTA — 20 dias
                proxima_avaliacao_em=AGORA + timedelta(days=20),
                laboratorio_id=lab1,
            ),
            _aval(  # NONE — 200 dias
                proxima_avaliacao_em=AGORA + timedelta(days=200),
                laboratorio_id=lab2,
            ),
            _aval(  # P1_VENCIDA — vencida ha 10 dias
                proxima_avaliacao_em=AGORA - timedelta(days=10),
                laboratorio_id=lab3,
            ),
        ]
        alertas = executar(ultimas_avaliacoes=avals, agora=AGORA)
        assert len(alertas) == 2
        labs_alertados = {a.laboratorio_id for a in alertas}
        assert labs_alertados == {lab1, lab3}
        sevs = {a.severidade for a in alertas}
        assert sevs == {"P2_ALERTA", "P1_VENCIDA"}

    def test_agora_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            executar(
                ultimas_avaliacoes=[],
                agora=datetime(2026, 6, 30, 12, 0),
            )

    def test_alerta_preserva_correlation_id(self) -> None:
        aval = _aval(proxima_avaliacao_em=AGORA + timedelta(days=15))
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        assert alertas[0].correlation_id == aval.correlation_id

    def test_alerta_carrega_metadata_completa(self) -> None:
        avaliado = datetime(2025, 6, 30, 0, 0, tzinfo=UTC)
        proxima = AGORA + timedelta(days=10)
        aval = _aval(
            proxima_avaliacao_em=proxima,
            avaliado_em=avaliado,
        )
        alertas = executar(ultimas_avaliacoes=[aval], agora=AGORA)
        alerta = alertas[0]
        assert alerta.laboratorio_id == aval.laboratorio_id
        assert alerta.tenant_id == aval.tenant_id
        assert alerta.avaliacao_id == aval.id
        assert alerta.avaliado_em_anterior == avaliado
        assert alerta.proxima_avaliacao_em == proxima
        assert alerta.dias_restantes == 10
