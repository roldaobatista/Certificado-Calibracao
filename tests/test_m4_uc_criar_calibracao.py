"""Testes use case `criar_calibracao` (P4 Fase 5 Batch A — T-CAL-077).

Use case puro testado com FakeCalibracaoRepository — sem Django, sem DB.
Casos cobertos:
  - Happy ATIVIDADE_OS (com atividade_os_id NOT NULL).
  - Happy AVULSA (sem atividade_os_id).
  - Rejeicao origem=ATIVIDADE_OS sem atividade_os_id (ADR-0023).
  - Rejeicao origem=AVULSA com atividade_os_id (ADR-0023).
  - Rejeicao cliente_referencia_hash vazio (ADR-0032).
  - Rejeicao cliente_key_id vazio (ADR-0064).
  - Rejeicao datetime sem tz (INV-VIG-004).
  - Snapshot retornado em RECEPCIONADA + revision=0 (INV-CAL-WORM-001).
  - Snapshot tem numero_interno alocado pelo repo.
  - Defaults PG refletidos no snapshot pos-criacao.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.criar_calibracao import (
    CriarCalibracaoInput,
    executar,
)
from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)

# =====================================================================
# FakeCalibracaoRepository — implementa Protocol em memoria
# =====================================================================


@dataclass
class FakeCalibracaoRepository:
    """In-memory repo pra testes — implementa CalibracaoRepository."""

    snapshots: dict[UUID, CalibracaoSnapshot] = field(default_factory=dict)
    proximo_numero: int = 1

    def obter_por_id(self, calibracao_id: UUID) -> CalibracaoSnapshot | None:
        return self.snapshots.get(calibracao_id)

    def proximo_numero_interno(self) -> int:
        n = self.proximo_numero
        self.proximo_numero += 1
        return n

    def salvar_nova(self, snapshot: CalibracaoSnapshot) -> None:
        if snapshot.id in self.snapshots:
            raise ValueError(f"duplicate id {snapshot.id}")
        self.snapshots[snapshot.id] = snapshot

    def atualizar_com_lock(
        self, snapshot: CalibracaoSnapshot, revision_anterior: int
    ) -> bool:
        atual = self.snapshots.get(snapshot.id)
        if atual is None:
            return False
        if atual.revision != revision_anterior:
            return False
        self.snapshots[snapshot.id] = snapshot
        return True


def _input_base(**overrides: object) -> CriarCalibracaoInput:
    """Builder de input com defaults sensatos."""
    defaults: dict[str, object] = {
        "tenant_id": uuid4(),
        "origem_recepcao": OrigemRecepcao.AVULSA,
        "atividade_os_id": None,
        "instrumento_id": uuid4(),
        "snapshot_equipamento_json": {"nome": "Balanca AS6000", "ns": "SN-12345"},
        "cliente_id": uuid4(),
        "cliente_referencia_hash": "v01$aGVsbG8=",
        "cliente_key_id": "cliente-key-v1",
        "tipo_acreditacao": TipoAcreditacao.NAO_RBC,
        "recepcionada_em": datetime(2026, 5, 25, 14, 0, tzinfo=UTC),
        "correlation_id": uuid4(),
        "criada_por_user_id": uuid4(),
        "causation_id": None,
    }
    defaults.update(overrides)
    return CriarCalibracaoInput(**defaults)  # type: ignore[arg-type]


# =====================================================================
# Happy path
# =====================================================================


class TestHappyPath:
    def test_avulsa_cria_em_recepcionada(self) -> None:
        repo = FakeCalibracaoRepository()
        out = executar(_input_base(), repo)
        snap = out.snapshot
        assert snap.status == EstadoCalibracao.RECEPCIONADA
        assert snap.revision == 0
        assert snap.origem_recepcao == OrigemRecepcao.AVULSA
        assert snap.atividade_os_id is None
        assert snap.numero_interno == 1
        assert snap.numero_exibido == ""  # trigger PG preenche

    def test_atividade_os_cria_com_vinculo(self) -> None:
        repo = FakeCalibracaoRepository()
        atividade_id = uuid4()
        out = executar(
            _input_base(
                origem_recepcao=OrigemRecepcao.ATIVIDADE_OS,
                atividade_os_id=atividade_id,
            ),
            repo,
        )
        assert out.snapshot.origem_recepcao == OrigemRecepcao.ATIVIDADE_OS
        assert out.snapshot.atividade_os_id == atividade_id

    def test_numero_interno_incremental(self) -> None:
        repo = FakeCalibracaoRepository()
        out1 = executar(_input_base(), repo)
        out2 = executar(_input_base(), repo)
        out3 = executar(_input_base(), repo)
        assert out1.snapshot.numero_interno == 1
        assert out2.snapshot.numero_interno == 2
        assert out3.snapshot.numero_interno == 3

    def test_persistencia_no_repo(self) -> None:
        repo = FakeCalibracaoRepository()
        out = executar(_input_base(), repo)
        assert repo.obter_por_id(out.snapshot.id) == out.snapshot

    def test_defaults_pg_refletidos_no_snapshot(self) -> None:
        """Snapshot pos-criacao reflete defaults PG aplicaveis."""
        repo = FakeCalibracaoRepository()
        out = executar(_input_base(), repo)
        snap = out.snapshot
        # regra_decisao default ACEITACAO_SIMPLES no PG
        assert snap.regra_decisao == RegraDecisao.ACEITACAO_SIMPLES
        # Sem acordo do cliente ainda
        assert snap.regra_decisao_acordada_em is None
        assert snap.regra_decisao_acordada_documento_id is None
        # Sem motor de calculo ainda
        assert snap.versao_motor_calculo == ""

    def test_correlation_id_preservado(self) -> None:
        repo = FakeCalibracaoRepository()
        corr = uuid4()
        out = executar(_input_base(correlation_id=corr), repo)
        assert out.snapshot.correlation_id == corr

    def test_causation_id_opcional(self) -> None:
        repo = FakeCalibracaoRepository()
        original = uuid4()
        out = executar(_input_base(causation_id=original), repo)
        assert out.snapshot.causation_id == original

    def test_rbc_carrega_tipo_acreditacao(self) -> None:
        repo = FakeCalibracaoRepository()
        out = executar(_input_base(tipo_acreditacao=TipoAcreditacao.RBC), repo)
        assert out.snapshot.tipo_acreditacao == TipoAcreditacao.RBC

    def test_snapshot_equipamento_capturado(self) -> None:
        repo = FakeCalibracaoRepository()
        snap_eq = {"nome": "Termometro X", "ns": "T-2026"}
        out = executar(_input_base(snapshot_equipamento_json=snap_eq), repo)
        assert out.snapshot.snapshot_equipamento_json == snap_eq

    def test_criada_por_user_id_preservado(self) -> None:
        repo = FakeCalibracaoRepository()
        user = uuid4()
        out = executar(_input_base(criada_por_user_id=user), repo)
        assert out.snapshot.criada_por_user_id == user


# =====================================================================
# Validacoes ADR-0023 (origem vs atividade_os_id)
# =====================================================================


class TestAdr0023Vinculacao:
    def test_rejeita_atividade_os_sem_id(self) -> None:
        with pytest.raises(ValueError, match="atividade_os_id NOT NULL"):
            _input_base(
                origem_recepcao=OrigemRecepcao.ATIVIDADE_OS,
                atividade_os_id=None,
            )

    def test_rejeita_avulsa_com_id(self) -> None:
        with pytest.raises(ValueError, match="proibe atividade_os_id"):
            _input_base(
                origem_recepcao=OrigemRecepcao.AVULSA,
                atividade_os_id=uuid4(),
            )


# =====================================================================
# Validacoes ADR-0032 + INV-VIG-004
# =====================================================================


class TestValidacoesInput:
    def test_rejeita_cliente_referencia_hash_vazio(self) -> None:
        with pytest.raises(ValueError, match="cliente_referencia_hash"):
            _input_base(cliente_referencia_hash="")

    def test_rejeita_cliente_key_id_vazio(self) -> None:
        with pytest.raises(ValueError, match="cliente_key_id"):
            _input_base(cliente_key_id="")

    def test_rejeita_datetime_sem_tz(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            _input_base(recepcionada_em=datetime(2026, 5, 25, 14, 0))  # sem tzinfo


# =====================================================================
# Snapshot imutabilidade
# =====================================================================


def test_snapshot_eh_frozen() -> None:
    """CalibracaoSnapshot eh dataclass(frozen=True) — nao muta."""
    from dataclasses import FrozenInstanceError

    repo = FakeCalibracaoRepository()
    out = executar(_input_base(), repo)
    with pytest.raises(FrozenInstanceError):
        out.snapshot.status = EstadoCalibracao.APROVADA  # type: ignore[misc]


def test_repository_protocol_compativel_com_fake() -> None:
    """FakeCalibracaoRepository implementa o Protocol CalibracaoRepository."""
    from src.domain.metrologia.calibracao.repository import CalibracaoRepository

    repo = FakeCalibracaoRepository()
    assert isinstance(repo, CalibracaoRepository)
