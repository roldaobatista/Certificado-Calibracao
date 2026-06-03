"""Portas (Protocols) de persistência — domínio define, infra implementa (ADR-0007).

Sem Django. Os use cases (Fatia 2) dependem destes Protocols; a Fatia 1b fornece as
implementações Django aninhadas (ADR-0072)."""

from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID

from .entities import (
    AlertaVencimento,
    BloqueioOperacional,
    DocumentoRegulatorio,
    EventoEmergencial,
    RevisaoDocumento,
)


class DocumentoRegulatorioRepository(Protocol):
    def salvar_novo(
        self, documento: DocumentoRegulatorio, revisao_inicial: RevisaoDocumento
    ) -> None:
        """Persiste o documento + revisão v1 numa transação (caller envolve atomic)."""
        ...

    def obter_por_id(self, *, tenant_id: UUID, documento_id: UUID) -> DocumentoRegulatorio | None: ...

    def existe_chave(
        self, *, tenant_id: UUID, tipo: str, numero: str, orgao_emissor: str
    ) -> bool:
        """Idempotência de cadastro (mesmo tipo+número+órgão no tenant)."""
        ...

    def obter_por_chave_natural(
        self, *, tenant_id: UUID, tipo: str, numero: str, orgao_emissor: str
    ) -> DocumentoRegulatorio | None:
        """Reconstrói o documento pela chave natural (retentativa idempotente da
        promoção D-LIC-4 — devolve o existente sem re-promover)."""
        ...

    def atualizar_vigencia_cache(
        self,
        *,
        tenant_id: UUID,
        documento_id: UUID,
        vigencia_inicio: date,
        vigencia_fim: date,
    ) -> None:
        """Renovação: avança a vigência da raiz + recalcula `status_cache` (Padrão B
        mutável — a revisão append-only é gravada à parte)."""
        ...


class RevisaoRepository(Protocol):
    def append(self, revisao: RevisaoDocumento) -> None:
        """WORM append-only (INV-LIC-WORM-001) — nunca update/delete."""
        ...

    def listar_por_documento(
        self, *, tenant_id: UUID, documento_id: UUID
    ) -> list[RevisaoDocumento]: ...

    def proximo_numero_revisao(self, *, tenant_id: UUID, documento_id: UUID) -> int: ...


class AlertaRepository(Protocol):
    def agendar(self, alerta: AlertaVencimento) -> None:
        """Idempotente por (tenant, documento, janela_dias) — UNIQUE na Fatia 1b."""
        ...

    def cancelar_pendentes(self, *, tenant_id: UUID, documento_id: UUID) -> int:
        """Cancela alertas PENDENTES ao renovar (reagenda na nova vigência)."""
        ...


class BloqueioRepository(Protocol):
    def abrir(self, bloqueio: BloqueioOperacional) -> None: ...

    def resolver_ativos(
        self, *, tenant_id: UUID, documento_id: UUID, em: date
    ) -> int:
        """Auto-resolve bloqueios ativos do documento ao renovar (data_fim_bloqueio)."""
        ...

    def obter_ativo(
        self, *, tenant_id: UUID, documento_id: UUID
    ) -> BloqueioOperacional | None: ...


class EventoEmergencialRepository(Protocol):
    def registrar(self, evento: EventoEmergencial) -> None:
        """WORM append-only (INV-033 / INV-LIC-WORM-001) — liberação auditada."""
        ...
