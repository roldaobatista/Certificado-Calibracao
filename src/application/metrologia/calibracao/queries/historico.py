"""T-CAL-108 — HistoricoCalibracaoPorInstrumentoQueryService.

Lista calibracoes de um Equipamento (M2) ordenadas cronologicamente
DECRESCENTE (mais recente primeiro), com paginacao por janela.

Budget de performance: <= 500ms na implementacao Django (Fase 8) com
indice (tenant_id, instrumento_id, criada_em DESC). Aqui apenas a
funcao pura sobre snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao


@dataclass(frozen=True, slots=True)
class ItemHistoricoCalibracao:
    """Linha do historico (snapshot enxuto para listagem)."""

    calibracao_id: UUID
    tenant_id: UUID
    numero_exibido: str
    instrumento_id: UUID
    status: EstadoCalibracao
    criada_em: datetime
    revision: int
    executor_id: UUID | None
    revisor_id: UUID | None


@dataclass(frozen=True, slots=True)
class HistoricoCalibracaoPagina:
    """Pagina do historico (resposta paginada)."""

    itens: tuple[ItemHistoricoCalibracao, ...]
    total: int  # total absoluto antes de paginar
    pagina: int  # 1-based
    tamanho_pagina: int
    tem_proxima: bool


def executar(
    *,
    instrumento_id: UUID,
    calibracoes: list[CalibracaoSnapshot],
    tenant_id: UUID | None = None,
    pagina: int = 1,
    tamanho_pagina: int = 20,
    status_incluir: frozenset[EstadoCalibracao] | None = None,
) -> HistoricoCalibracaoPagina:
    """Historico de calibracoes de um instrumento.

    Args:
      instrumento_id: equipamento alvo (FK Equipamento M2).
      calibracoes: snapshots ja carregados (caller usa ORM filter).
      tenant_id: filtro adicional defensivo.
      pagina: 1-based.
      tamanho_pagina: maximo 100 por requisicao.
      status_incluir: se None, inclui todos os estados. Se vier, filtra.

    Returns:
      HistoricoCalibracaoPagina com itens ordenados criada_em DESC.
    """
    if pagina < 1:
        raise ValueError("historico: pagina deve ser >= 1")
    if tamanho_pagina < 1 or tamanho_pagina > 100:
        raise ValueError("historico: tamanho_pagina deve estar em [1, 100]")

    filtradas = [
        c
        for c in calibracoes
        if c.instrumento_id == instrumento_id
        and (tenant_id is None or c.tenant_id == tenant_id)
        and (status_incluir is None or c.status in status_incluir)
    ]
    filtradas.sort(key=lambda c: c.criada_em, reverse=True)

    total = len(filtradas)
    inicio = (pagina - 1) * tamanho_pagina
    fim = inicio + tamanho_pagina
    janela = filtradas[inicio:fim]

    itens = tuple(
        ItemHistoricoCalibracao(
            calibracao_id=c.id,
            tenant_id=c.tenant_id,
            numero_exibido=c.numero_exibido,
            instrumento_id=c.instrumento_id,
            status=c.status,
            criada_em=c.criada_em,
            revision=c.revision,
            executor_id=c.executor_id,
            revisor_id=c.revisor_id,
        )
        for c in janela
    )

    return HistoricoCalibracaoPagina(
        itens=itens,
        total=total,
        pagina=pagina,
        tamanho_pagina=tamanho_pagina,
        tem_proxima=fim < total,
    )
