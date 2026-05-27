"""Tests T-CAL-118 — analisar_padrao_medicoes_controle.

P-CAL-R8 RBC + ISO 17025 cl. 7.7.1 — Western Electric trigger por INSERT.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.application.metrologia.calibracao.jobs.analisar_padrao_medicoes_controle import (
    executar,
)
from src.domain.metrologia.calibracao.entities import MedicaoControleSnapshot


def _med(
    *,
    z: Decimal | None,
    tenant_id: UUID,
    padrao_id: UUID,
    grandeza: str = "massa",
    executado_em: datetime | None = None,
) -> MedicaoControleSnapshot:
    return MedicaoControleSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
        padrao_id=padrao_id,
        grandeza=grandeza,
        valor_medido=Decimal("100"),
        valor_esperado=Decimal("100"),
        desvio=Decimal("0"),
        dentro_2sigma=True,
        dentro_3sigma=True,
        escore_z=z,
        regra_western_electric_violada="",
        executor_id_hash="v01$exec",
        executado_em=executado_em or datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
        correlation_id=uuid4(),
    )


class TestAnalisarMedicoes:
    def test_janela_sem_violacao_retorna_none(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        janela = [
            _med(z=Decimal("0.5"), tenant_id=tenant, padrao_id=padrao),
            _med(z=Decimal("-0.3"), tenant_id=tenant, padrao_id=padrao),
            _med(z=Decimal("0.1"), tenant_id=tenant, padrao_id=padrao),
        ]
        recente = janela[-1]
        assert executar(medicao_recente=recente, janela_cronologica=janela) is None

    def test_z_recente_acima_3sigma_dispara_rule1(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        recente = _med(z=Decimal("3.5"), tenant_id=tenant, padrao_id=padrao)
        janela = [recente]
        acao = executar(medicao_recente=recente, janela_cronologica=janela)
        assert acao is not None
        assert acao.regra_violada == "RULE_1_3SIGMA"
        assert acao.severidade == "P1_RULE1"
        assert acao.medicao_id == recente.id

    def test_outras_regras_severidade_p2(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        # 7 pos consecutivos -> RULE_2_SEVEN_SAME_SIDE
        janela = [
            _med(
                z=Decimal(f"0.{(i % 9) + 1}"),
                tenant_id=tenant,
                padrao_id=padrao,
                executado_em=datetime(2026, 6, 30, 12, i, tzinfo=UTC),
            )
            for i in range(7)
        ]
        recente = janela[-1]
        acao = executar(medicao_recente=recente, janela_cronologica=janela)
        assert acao is not None
        assert acao.regra_violada == "RULE_2_SEVEN_SAME_SIDE"
        assert acao.severidade == "P2_OUTRAS_REGRAS"

    def test_recente_sem_z_score_nao_avalia(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        # Mesmo com janela violando RULE_1, sem z_score na recente nao avalia
        janela = [
            _med(z=Decimal("3.5"), tenant_id=tenant, padrao_id=padrao),
            _med(z=None, tenant_id=tenant, padrao_id=padrao),
        ]
        recente = janela[-1]
        assert executar(medicao_recente=recente, janela_cronologica=janela) is None

    def test_filtra_tenant_diferente(self) -> None:
        tenant_a, tenant_b, padrao = uuid4(), uuid4(), uuid4()
        recente = _med(z=Decimal("0.5"), tenant_id=tenant_a, padrao_id=padrao)
        janela = [
            _med(z=Decimal("3.5"), tenant_id=tenant_b, padrao_id=padrao),  # ignora
            recente,
        ]
        acao = executar(medicao_recente=recente, janela_cronologica=janela)
        # Sem RULE_1 no tenant_a (so 1 ponto z=0.5), retorna None
        assert acao is None

    def test_filtra_padrao_diferente(self) -> None:
        tenant, padrao_a, padrao_b = uuid4(), uuid4(), uuid4()
        recente = _med(z=Decimal("0.5"), tenant_id=tenant, padrao_id=padrao_a)
        janela = [
            _med(z=Decimal("3.5"), tenant_id=tenant, padrao_id=padrao_b),  # ignora
            recente,
        ]
        assert executar(medicao_recente=recente, janela_cronologica=janela) is None

    def test_filtra_grandeza_diferente(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        recente = _med(
            z=Decimal("0.5"),
            tenant_id=tenant,
            padrao_id=padrao,
            grandeza="massa",
        )
        janela = [
            _med(
                z=Decimal("3.5"),
                tenant_id=tenant,
                padrao_id=padrao,
                grandeza="temperatura",
            ),
            recente,
        ]
        assert executar(medicao_recente=recente, janela_cronologica=janela) is None

    def test_filtra_snap_sem_zscore_na_janela(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        recente = _med(z=Decimal("0.5"), tenant_id=tenant, padrao_id=padrao)
        janela = [
            _med(z=None, tenant_id=tenant, padrao_id=padrao),  # ignora
            recente,
        ]
        assert executar(medicao_recente=recente, janela_cronologica=janela) is None

    def test_janela_vazia_pos_filtragem_retorna_none(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        recente = _med(z=Decimal("3.5"), tenant_id=tenant, padrao_id=padrao)
        outro_tenant = uuid4()
        janela = [
            _med(z=Decimal("3.5"), tenant_id=outro_tenant, padrao_id=padrao),
        ]
        # `recente` NAO esta na janela; depois de filtrar fica vazia
        acao = executar(medicao_recente=recente, janela_cronologica=janela)
        assert acao is None

    def test_acao_carrega_correlation_id_da_recente(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        recente = _med(z=Decimal("3.5"), tenant_id=tenant, padrao_id=padrao)
        janela = [recente]
        acao = executar(medicao_recente=recente, janela_cronologica=janela)
        assert acao is not None
        assert acao.correlation_id == recente.correlation_id

    def test_acao_janela_size_reflete_pos_filtragem(self) -> None:
        tenant, padrao = uuid4(), uuid4()
        outro_tenant = uuid4()
        recente = _med(z=Decimal("3.5"), tenant_id=tenant, padrao_id=padrao)
        janela = [
            _med(z=Decimal("0.5"), tenant_id=outro_tenant, padrao_id=padrao),  # filtrado
            _med(z=Decimal("1.0"), tenant_id=tenant, padrao_id=padrao),
            recente,
        ]
        acao = executar(medicao_recente=recente, janela_cronologica=janela)
        assert acao is not None
        assert acao.janela_size == 2  # so as do tenant correto
