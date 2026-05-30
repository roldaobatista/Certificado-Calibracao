"""Protocols do repositório do domínio procedimentos-calibracao (M7 — T-PROC-013).

Use cases consomem estes Protocols; adapters Django concretos vivem em
src/infrastructure/metrologia/procedimentos_calibracao/repositories.py (Fatia 1b
— ADR-0072). A porta cross-módulo consumida pela calibração (`vigente_em`) NÃO é
singleton stateful — é função de módulo em `query_service.py` (C-3 / ADR-0073).
Convenção M5/M6: `obter_*` retorna snapshot ou None; mutação da raiz via CAS
(`atualizar_com_lock`); revogação one-shot; superseção via `encerrar_vigencia`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

from .entities import ProcedimentoSnapshot


@runtime_checkable
class ProcedimentoRepository(Protocol):
    """Raiz do agregado ProcedimentoCalibracao. CAS optimistic via `revision`."""

    def obter_por_id(self, procedimento_id: UUID) -> ProcedimentoSnapshot | None: ...

    def existe_chave(self, *, tenant_id: UUID, codigo: str, versao: int) -> bool:
        """INV-PROC-002 — UNIQUE documental `(tenant_id, codigo, versao)`."""
        ...

    def proxima_versao(self, *, tenant_id: UUID, codigo: str) -> int:
        """Próxima versão do código (revisão = INSERT nova versão — AC-CAL-016-3).
        1 se o código ainda não existe."""
        ...

    def salvar_novo(self, snapshot: ProcedimentoSnapshot) -> None:
        """INSERT (RASCUNHO na criação ou nova versão na revisão)."""
        ...

    def atualizar_com_lock(
        self, snapshot: ProcedimentoSnapshot, revision_anterior: int
    ) -> bool:
        """UPDATE CAS WHERE revision=esperada; rowcount=0 -> corrida (caller 409).

        NÃO muta campos técnicos de linha PUBLICADA (trigger PG bloqueia —
        INV-PROC-003); usado para editar rascunho e na transição de publicação.
        """
        ...

    def vigente_anterior(
        self,
        *,
        tenant_id: UUID,
        codigo: str,
        grandeza: Grandeza,
        faixa: FaixaMedicao,
    ) -> ProcedimentoSnapshot | None:
        """Versão PUBLICADA vigente (vigencia_fim NULL) da mesma chave natural —
        a ser encerrada na superseção (INV-PROC-008). None se não há."""
        ...

    def encerrar_vigencia(
        self, *, procedimento_id: UUID, vigencia_fim: datetime, revision_anterior: int
    ) -> bool:
        """Encerra a vigência da versão superada por N+1 (`vigencia_fim`
        NULL→valor, one-shot ADR-0030); CAS via `revision`. A linha NÃO é apagada
        (WORM Padrão B). False se corrida/já encerrada (caller 409)."""
        ...

    def revogar(
        self, *, procedimento_id: UUID, revogado_em: datetime, motivo: str
    ) -> bool:
        """Liga `revogado_em` + `motivo_revogacao` + estado REVOGADO (one-shot
        ADR-0031). False se não encontrado/já revogado."""
        ...

    def vigente_em(
        self,
        *,
        tenant_id: UUID,
        grandeza: Grandeza,
        faixa: FaixaMedicao,
        em: datetime,
    ) -> ProcedimentoSnapshot | None:
        """Procedimento PUBLICADO + vigente em `em` que CONTÉM a faixa para a
        grandeza (contenção total — INV-PROC-001). Filtro `tenant_id` EXPLÍCITO
        além da RLS (defesa em profundidade — molde M6). None = fail-closed
        (caller bloqueia RBC). Alimenta a porta `query_service.vigente_em`."""
        ...
