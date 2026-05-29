"""Testes P4 GATE-PAD-PORTA-M4 (T-PAD-031/032) — consumo da porta pelo M4.

Puros (Fakes): provam que o use case `registrar_padrao_usado` aplica o GATE
fail-closed ANTES de gravar — padrao bloqueado nunca vira PadraoUsado.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.application.metrologia.calibracao import registrar_padrao_usado as rpu
from src.domain.metrologia.padroes.entities import PadraoUsadoSnapshot
from src.domain.metrologia.padroes.enums import ClassePadrao, VinculacaoCadeia
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)

TENANT = uuid4()
CAL = uuid4()
PADRAO = uuid4()


def _snapshot() -> PadraoUsadoSnapshot:
    return PadraoUsadoSnapshot(
        padrao_id=PADRAO,
        numero_serie="PAD-1",
        fabricante="Mettler",
        modelo="XPR",
        classe=ClassePadrao.E2,
        vinculacao=VinculacaoCadeia.INMETRO,
        grandezas=(Grandeza.MASSA,),
        faixas=(FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),),
        incertezas_certificado=(
            IncertezaExpandida(Decimal("0.001"), Decimal("2"), Decimal("0.9545"), "g"),
        ),
        validade_certificado_rastreabilidade=date(2027, 1, 1),
    )


class FakeRepo:
    def __init__(self) -> None:
        self.salvos: list[rpu.PadraoUsadoWrite] = []

    def salvar_novo(self, write: rpu.PadraoUsadoWrite) -> None:
        self.salvos.append(write)


def _input(**kw: object) -> rpu.RegistrarPadraoUsadoInput:
    base: dict[str, object] = {
        "tenant_id": TENANT,
        "calibracao_id": CAL,
        "calibracao_status": "configurada",
        "tipo_acreditacao": "NAO_RBC",
        "padrao_id": PADRAO,
        "padrao_id_hash": "v1$pad",
        "tenant_e_perfil_a": False,
        "vinculacao_si_tipo": "INMETRO",
        "vinculacao_si_referencia_id": "INMETRO-MASSA-2024-1",
        "snapshot_capturado_at": datetime(2026, 6, 1, tzinfo=UTC),
    }
    base.update(kw)
    # mypy nao infere tipos via **dict[str, object] desempacotado em dataclass
    return rpu.RegistrarPadraoUsadoInput(**base)  # type: ignore[arg-type]


def test_gate_bloqueia_e_nao_grava():
    repo = FakeRepo()
    with pytest.raises(rpu.PadraoBloqueadoParaUsoError, match="recal vencido"):
        rpu.executar(
            _input(),
            bloqueado_checker=lambda _pid, _a: (True, "recal vencido"),
            snapshot_provider=lambda _pid: _snapshot(),
            repo=repo,
        )
    assert repo.salvos == []  # NUNCA grava padrao bloqueado


def test_gate_libera_e_grava():
    repo = FakeRepo()
    out = rpu.executar(
        _input(),
        bloqueado_checker=lambda _pid, _a: (False, ""),
        snapshot_provider=lambda _pid: _snapshot(),
        repo=repo,
    )
    assert len(repo.salvos) == 1
    assert out.write.padrao_id == PADRAO
    assert repo.salvos[0].snapshot.numero_serie == "PAD-1"


def test_status_invalido_nem_chega_no_gate():
    repo = FakeRepo()
    chamou = {"checker": False}

    def _checker(_pid: object, _a: object) -> tuple[bool, str]:
        chamou["checker"] = True
        return (False, "")

    with pytest.raises(rpu.CalibracaoNaoAceitaSnapshotError):
        rpu.executar(
            _input(calibracao_status="aprovada"),
            bloqueado_checker=_checker,
            snapshot_provider=lambda _pid: _snapshot(),
            repo=repo,
        )
    assert chamou["checker"] is False
    assert repo.salvos == []


def test_rbc_proibe_interno_declarado():
    repo = FakeRepo()
    with pytest.raises(rpu.RBCProibeInternoDeclaradoError):
        rpu.executar(
            _input(tipo_acreditacao="RBC", vinculacao_si_tipo="INTERNO_DECLARADO"),
            bloqueado_checker=lambda _pid, _a: (False, ""),
            snapshot_provider=lambda _pid: _snapshot(),
            repo=repo,
        )
    assert repo.salvos == []


def test_snapshot_ausente_bloqueia():
    repo = FakeRepo()
    with pytest.raises(rpu.PadraoSemSnapshotError):
        rpu.executar(
            _input(),
            bloqueado_checker=lambda _pid, _a: (False, ""),
            snapshot_provider=lambda _pid: None,
            repo=repo,
        )
    assert repo.salvos == []
