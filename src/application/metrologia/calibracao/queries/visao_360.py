"""T-CAL-106 — CalibracaoVisao360QueryService.

Agrega snapshot da Calibracao + entidades 1:N filhas em UM resultado
consolidado pra UI de visao 360 graus.

Budget de performance: <= 400ms na implementacao Django (Fase 8).
Aqui apenas a funcao pura sobre snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.domain.metrologia.calibracao.entities import (
    CalibracaoSnapshot,
    ComponenteIncertezaSnapshot,
    LeituraSnapshot,
    NaoConformidadeSnapshot,
    OrcamentoIncertezaSnapshot,
    ReclamacaoCalibracaoSnapshot,
)


@dataclass(frozen=True, slots=True)
class CalibracaoVisao360:
    """Snapshot consolidado pra UI."""

    calibracao: CalibracaoSnapshot
    leituras: tuple[LeituraSnapshot, ...]  # ordem cronologica
    orcamento: OrcamentoIncertezaSnapshot | None  # 0 ou 1
    componentes_orcamento: tuple[ComponenteIncertezaSnapshot, ...]
    nao_conformidades: tuple[NaoConformidadeSnapshot, ...]
    reclamacoes: tuple[ReclamacaoCalibracaoSnapshot, ...]

    @property
    def total_leituras(self) -> int:
        return len(self.leituras)

    @property
    def tem_nc_aberta(self) -> bool:
        """NC aberta = qualquer estado != FECHADA (REABERTA volta a CONTIDA)."""
        from src.domain.metrologia.calibracao.enums import EstadoNaoConformidade

        return any(
            nc.estado != EstadoNaoConformidade.FECHADA
            for nc in self.nao_conformidades
        )

    @property
    def tem_reclamacao_aberta(self) -> bool:
        from src.domain.metrologia.calibracao.enums import EstadoReclamacao

        return any(
            r.estado in {EstadoReclamacao.RECEBIDA, EstadoReclamacao.EM_ANALISE}
            for r in self.reclamacoes
        )


def executar(
    *,
    calibracao_id: UUID,
    calibracao: CalibracaoSnapshot,
    leituras: list[LeituraSnapshot],
    orcamento: OrcamentoIncertezaSnapshot | None,
    componentes_orcamento: list[ComponenteIncertezaSnapshot],
    nao_conformidades: list[NaoConformidadeSnapshot],
    reclamacoes: list[ReclamacaoCalibracaoSnapshot],
) -> CalibracaoVisao360:
    """Agrega snapshots em CalibracaoVisao360 — caller carrega via Django ORM.

    Filtra defensivamente: caller pode passar listas globais e a funcao
    isola apenas o que pertence a `calibracao_id` + `tenant_id`.
    """
    if calibracao.id != calibracao_id:
        raise ValueError(
            f"visao_360: calibracao_id={calibracao_id} != calibracao.id="
            f"{calibracao.id}"
        )

    tenant = calibracao.tenant_id

    leituras_filtradas = [
        leitura
        for leitura in leituras
        if leitura.tenant_id == tenant and leitura.calibracao_id == calibracao_id
    ]
    # ordem cronologica crescente
    leituras_filtradas.sort(key=lambda lt: lt.timestamp)

    if orcamento is not None:
        if orcamento.calibracao_id != calibracao_id:
            orcamento = None
        elif orcamento.tenant_id != tenant:
            orcamento = None

    componentes_filtrados: list[ComponenteIncertezaSnapshot] = []
    if orcamento is not None:
        componentes_filtrados = [
            c
            for c in componentes_orcamento
            if c.tenant_id == tenant
            and c.orcamento_incerteza_id == orcamento.id
        ]

    ncs_filtradas = [
        nc
        for nc in nao_conformidades
        if nc.tenant_id == tenant and nc.calibracao_id == calibracao_id
    ]
    reclamacoes_filtradas = [
        r
        for r in reclamacoes
        if r.tenant_id == tenant and r.calibracao_id == calibracao_id
    ]

    return CalibracaoVisao360(
        calibracao=calibracao,
        leituras=tuple(leituras_filtradas),
        orcamento=orcamento,
        componentes_orcamento=tuple(componentes_filtrados),
        nao_conformidades=tuple(ncs_filtradas),
        reclamacoes=tuple(reclamacoes_filtradas),
    )
