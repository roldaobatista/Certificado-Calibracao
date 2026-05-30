"""Protocols dos repositórios do domínio escopos-cmc (M6 T-ECMC-005).

Use cases consomem estes Protocols; adapters Django concretos vivem em
src/infrastructure/metrologia/escopos_cmc/repositories.py (Fatia 1b — ADR-0072).
A porta cross-módulo consumida pela calibração (`cobre`/`cmc_para`) NÃO é
singleton stateful — é função de módulo em `query_service.py` (TL-C-04 / ADR-0073).
Convenção M4/M5: `obter_*` retorna snapshot ou None; mutação da raiz via CAS
(`atualizar_com_lock`); revogação one-shot.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

from .entities import EscopoCMCSnapshot, EscopoExtraido


@runtime_checkable
class EscopoRepository(Protocol):
    """Raiz do agregado EscopoCMC. CAS optimistic via `revision`."""

    def obter_por_id(self, escopo_id: UUID) -> EscopoCMCSnapshot | None: ...

    def existe_chave_confirmada(
        self,
        *,
        tenant_id: UUID,
        grandeza: Grandeza,
        faixa: FaixaMedicao,
        procedimento_id: UUID | None,
        versao: int,
    ) -> bool:
        """INV-ECMC-001 — UNIQUE (tenant, grandeza, faixa_min, faixa_max,
        procedimento_id, versao)."""
        ...

    def proxima_versao(
        self,
        *,
        tenant_id: UUID,
        grandeza: Grandeza,
        faixa: FaixaMedicao,
        procedimento_id: UUID | None,
    ) -> int:
        """Próxima versão para a chave natural (revisão = INSERT nova versão —
        AC-CAL-015-2 / TL-C-07). 1 se não existe nenhuma."""
        ...

    def salvar_novo(self, snapshot: EscopoCMCSnapshot) -> None:
        """INSERT (CONFIRMADO ou RASCUNHO_EXTRAIDO conforme estado)."""
        ...

    def atualizar_com_lock(
        self, snapshot: EscopoCMCSnapshot, revision_anterior: int
    ) -> bool:
        """UPDATE CAS WHERE revision=esperada; rowcount=0 -> corrida (caller 409).

        NÃO muta campos metrológicos de linha CONFIRMADA (trigger PG bloqueia —
        INV-ECMC-003); usado para confirmar rascunho e revogar (one-shot).
        """
        ...

    def revogar(
        self, *, escopo_id: UUID, revogado_em: datetime, motivo: str
    ) -> bool:
        """Liga `revogado_em` + `motivo_revogacao` + estado REVOGADO (one-shot
        ADR-0031). False se não encontrado/já revogado."""
        ...

    def encerrar_vigencia(
        self, *, escopo_id: UUID, vigencia_fim: datetime, revision_anterior: int
    ) -> bool:
        """Encerra a vigência de uma versão superada por revisão (`vigencia_fim`
        NULL→valor, one-shot ADR-0030); CAS via `revision`. A linha NÃO é apagada
        (WORM Padrão B). False se corrida/já encerrada (caller 409)."""
        ...

    def listar_confirmados_vigentes(
        self, *, tenant_id: UUID, grandeza: Grandeza, em: datetime
    ) -> list[EscopoCMCSnapshot]:
        """Escopos CONFIRMADO + vigentes em `em` para a grandeza — alimenta
        `cobre()`/`cmc_para()`. Filtro `tenant_id` EXPLÍCITO além da RLS
        (defesa em profundidade — molde M5)."""
        ...


@runtime_checkable
class EscopoExtraidoRepository(Protocol):
    """Staging da extração de PDF (decisão N / Fatia 4). Mutável, NÃO WORM."""

    def salvar_novo(self, snapshot: EscopoExtraido) -> None: ...

    def obter_por_id(self, extraido_id: UUID) -> EscopoExtraido | None: ...

    def marcar_confirmado(
        self, *, extraido_id: UUID, confirmado_em: datetime, por_id_hash: str
    ) -> bool: ...
