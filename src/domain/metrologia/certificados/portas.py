"""Portas (Protocols) injetadas no domínio certificados (ADR-0073).

A validação de cobertura metrológica roda no USE CASE (não no permission layer
DRF), consumindo estado persistido via portas. Aqui só o CONTRATO; o adapter
real vive em `infrastructure/metrologia/certificados/` (Fatia 2). Fail-closed:
`None` significa "sem CMC no ponto" (ponto fora do escopo RBC vigente).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.metrologia.calibracao.entities import OrcamentoPorPontoSnapshot
from src.domain.metrologia.value_objects import Grandeza


@runtime_checkable
class LeituraOrcamentoPorPontoPort(Protocol):
    """Read-model `U(ponto)` da calibração (ADR-0077). Retorna TODOS os
    `OrcamentoPorPontoSnapshot` da calibração; o avaliador `reconciliar_pontos`
    indexa por `ponto_calibracao` e detecta duplicidade (`ORCAMENTO_PONTO_AMBIGUO`)
    ou ausência (`SEM_ORCAMENTO`) — lookup 1:1 fail-closed (INV-CER-RECONCILIA-005).
    """

    def __call__(
        self, *, tenant_id: UUID, calibracao_id: UUID
    ) -> Sequence[OrcamentoPorPontoSnapshot]: ...


@runtime_checkable
class CmcParaPort(Protocol):
    """2ª porta de EMISSÃO da cobertura RBC (distinta de `cmc_cobre`/config M6):
    a MENOR CMC acreditada vigente no ponto, ou `None` se o ponto não é coberto
    por escopo RBC vigente na data (fail-closed). ADR-0074 cond. 2 / INV-ECMC-009
    — fecha GATE-ECMC-U-MAIOR-CMC.

    O adapter (Fatia 2) faz a ponte com `escopos_cmc.query_service.cmc_para`
    (que recebe `grandeza: str`, `ponto: Decimal|str`, `data: datetime`):
    converte `Grandeza→.value` e `date→datetime`.
    """

    def __call__(
        self, *, tenant_id: UUID, grandeza: Grandeza, ponto: Decimal, data: date
    ) -> Decimal | None: ...
