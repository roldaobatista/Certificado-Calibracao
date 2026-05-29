"""Use case `registrar_padrao_usado` — GATE-PAD-PORTA-M4 (M5 T-PAD-031).

Ponto de consumo da porta `metrologia/padroes` pelo M4 (ADR-0040 + D-PAD-5).
ANTES de gravar `PadraoUsado` numa calibracao, o M4 chama
`padrao_bloqueado_para_uso` (porta fail-CLOSED) — padrao vencido/VI-reprovada/
PT-rejeitada/carta-violada/recal-pendente/origem-revogada NUNCA entra numa
calibracao (fecha o vetor de sinistro E&O — corretora FURO).

Use case PURO (ADR-0007): a porta entra como callables injetados
(`bloqueado_checker`/`snapshot_provider`) e a persistencia via
`PadraoUsadoRepository` Protocol. A view/consumer (Wave A — PadraoViewSet /
iniciar_leituras) faz o wiring com `query_service.padrao_bloqueado_para_uso` e
`query_service.snapshot_para_uso`.

Delegacao C-15 (explicita): a adequacao faixa/grandeza<->ponto de calibracao e
decidida no M4 (onde o ponto existe), NAO na porta de saude do padrao. O
snapshot expoe grandezas/faixas/incertezas pro M4 decidir.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.metrologia.padroes.entities import PadraoUsadoSnapshot

# Estados da calibracao que aceitam captura de snapshot de padrao
# (INV-CAL-RT-COMP-001 — snapshot nao retroativo; trigger PG tambem barra).
_STATUS_ACEITA_SNAPSHOT = frozenset({"recepcionada", "configurada"})


class PadraoBloqueadoParaUsoError(Exception):
    """GATE-PAD-PORTA-M4: a porta vetou o uso do padrao nesta calibracao."""

    def __init__(self, padrao_id: UUID, motivo: str) -> None:
        self.padrao_id = padrao_id
        self.motivo = motivo
        super().__init__(
            f"Padrao {padrao_id} bloqueado para uso em calibracao: {motivo}"
        )


class PadraoSemSnapshotError(Exception):
    def __init__(self, padrao_id: UUID) -> None:
        self.padrao_id = padrao_id
        super().__init__(f"Padrao {padrao_id} sem snapshot disponivel (inexistente/RLS).")


class CalibracaoNaoAceitaSnapshotError(Exception):
    """INV-CAL-RT-COMP-001 — snapshot so em recepcionada/configurada."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(
            f"Calibracao em '{status}' nao aceita captura de padrao usado "
            f"(INV-CAL-RT-COMP-001 — apenas recepcionada/configurada)."
        )


class RBCProibeInternoDeclaradoError(Exception):
    """INV-CAL-RAST-002 — tenant RBC nao usa padrao INTERNO_DECLARADO."""

    def __init__(self) -> None:
        super().__init__(
            "INV-CAL-RAST-002: calibracao RBC nao admite padrao com vinculacao "
            "SI INTERNO_DECLARADO (rastreabilidade insuficiente)."
        )


@dataclass(frozen=True, slots=True)
class PadraoUsadoWrite:
    """Intencao de escrita do PadraoUsado (adapter serializa pro JSONField)."""

    tenant_id: UUID
    calibracao_id: UUID
    padrao_id: UUID
    padrao_id_hash: str
    snapshot: PadraoUsadoSnapshot
    snapshot_capturado_at: datetime
    vinculacao_si_tipo: str
    vinculacao_si_referencia_id: str


@runtime_checkable
class PadraoUsadoRepository(Protocol):
    def salvar_novo(self, write: PadraoUsadoWrite) -> None: ...


@dataclass(frozen=True, slots=True)
class RegistrarPadraoUsadoInput:
    tenant_id: UUID
    calibracao_id: UUID
    calibracao_status: str
    tipo_acreditacao: str  # "RBC" | "NAO_RBC"
    padrao_id: UUID
    padrao_id_hash: str
    tenant_e_perfil_a: bool
    vinculacao_si_tipo: str
    vinculacao_si_referencia_id: str
    snapshot_capturado_at: datetime

    def __post_init__(self) -> None:
        if self.snapshot_capturado_at.tzinfo is None:
            raise ValueError("snapshot_capturado_at exige datetime tz-aware.")
        if not self.padrao_id_hash:
            raise ValueError("padrao_id_hash obrigatorio (HashVersionado ADR-0064).")


@dataclass(frozen=True, slots=True)
class RegistrarPadraoUsadoOutput:
    write: PadraoUsadoWrite


def executar(
    inp: RegistrarPadraoUsadoInput,
    *,
    bloqueado_checker: Callable[[UUID, bool], tuple[bool, str]],
    snapshot_provider: Callable[[UUID], PadraoUsadoSnapshot | None],
    repo: PadraoUsadoRepository,
) -> RegistrarPadraoUsadoOutput:
    """Aplica o GATE fail-closed e grava o PadraoUsado.

    Ordem deliberada: status -> GATE (porta) -> snapshot -> INV-CAL-RAST-002 ->
    persistencia. O GATE vem antes de qualquer escrita.
    """
    if inp.calibracao_status not in _STATUS_ACEITA_SNAPSHOT:
        raise CalibracaoNaoAceitaSnapshotError(inp.calibracao_status)

    # GATE-PAD-PORTA-M4 (fail-CLOSED) — antes de qualquer escrita.
    bloqueado, motivo = bloqueado_checker(inp.padrao_id, inp.tenant_e_perfil_a)
    if bloqueado:
        raise PadraoBloqueadoParaUsoError(inp.padrao_id, motivo)

    snapshot = snapshot_provider(inp.padrao_id)
    if snapshot is None:
        raise PadraoSemSnapshotError(inp.padrao_id)

    # INV-CAL-RAST-002 — RBC proibe INTERNO_DECLARADO.
    if inp.tipo_acreditacao == "RBC" and inp.vinculacao_si_tipo == "INTERNO_DECLARADO":
        raise RBCProibeInternoDeclaradoError

    write = PadraoUsadoWrite(
        tenant_id=inp.tenant_id,
        calibracao_id=inp.calibracao_id,
        padrao_id=inp.padrao_id,
        padrao_id_hash=inp.padrao_id_hash,
        snapshot=snapshot,
        snapshot_capturado_at=inp.snapshot_capturado_at,
        vinculacao_si_tipo=inp.vinculacao_si_tipo,
        vinculacao_si_referencia_id=inp.vinculacao_si_referencia_id,
    )
    repo.salvar_novo(write)
    return RegistrarPadraoUsadoOutput(write=write)
