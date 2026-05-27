"""Query: fila de calibracoes aguardando revisao / 2a conferencia.

Suporta 2 modos:
  - fila_revisor: calibracoes em EM_REVISAO_1 aguardando aprovar/rejeitar.
  - fila_conferente: calibracoes em AGUARDANDO_2A_CONFERENCIA aguardando
    aprovar 2a conferencia.

Ordenacao: criada_em CRESCENTE (FIFO — mais antigas primeiro).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao


@dataclass(frozen=True, slots=True)
class ItemFilaRevisao:
    """Linha da fila de revisor ou conferente."""

    calibracao_id: UUID
    tenant_id: UUID
    numero_exibido: str
    instrumento_id: UUID
    criada_em: datetime
    revision: int
    executor_id: UUID | None
    revisor_id: UUID | None  # None na fila do revisor; cravado na fila do conferente


def fila_revisor(
    *,
    calibracoes: list[CalibracaoSnapshot],
    tenant_id: UUID | None = None,
) -> list[ItemFilaRevisao]:
    """Calibracoes em EM_REVISAO_1 (aguardando aprovar/rejeitar revisao)."""
    itens: list[ItemFilaRevisao] = [
        ItemFilaRevisao(
            calibracao_id=c.id,
            tenant_id=c.tenant_id,
            numero_exibido=c.numero_exibido,
            instrumento_id=c.instrumento_id,
            criada_em=c.criada_em,
            revision=c.revision,
            executor_id=c.executor_id,
            revisor_id=c.revisor_id,
        )
        for c in calibracoes
        if c.status == EstadoCalibracao.EM_REVISAO_1
        and (tenant_id is None or c.tenant_id == tenant_id)
    ]
    itens.sort(key=lambda x: x.criada_em)
    return itens


def fila_conferente(
    *,
    calibracoes: list[CalibracaoSnapshot],
    tenant_id: UUID | None = None,
) -> list[ItemFilaRevisao]:
    """Calibracoes em AGUARDANDO_2A_CONFERENCIA."""
    itens: list[ItemFilaRevisao] = [
        ItemFilaRevisao(
            calibracao_id=c.id,
            tenant_id=c.tenant_id,
            numero_exibido=c.numero_exibido,
            instrumento_id=c.instrumento_id,
            criada_em=c.criada_em,
            revision=c.revision,
            executor_id=c.executor_id,
            revisor_id=c.revisor_id,
        )
        for c in calibracoes
        if c.status == EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA
        and (tenant_id is None or c.tenant_id == tenant_id)
    ]
    itens.sort(key=lambda x: x.criada_em)
    return itens
