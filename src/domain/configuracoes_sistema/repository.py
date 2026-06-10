"""Protocols de repositório do domínio `configuracoes-sistema` (Fatia 1a — T-CFG-015).

Interfaces (sem Django). Implementação Django na infra (Fatia 1b).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from .entities import (
    Empresa,
    Filial,
    Imposto,
    ReservaNumeroDocumento,
    SerieDocumento,
)
from .enums import TipoDocumento, TipoImposto


class EmpresaRepository(Protocol):
    def obter(self, *, tenant_id: UUID) -> Empresa | None: ...
    def salvar(self, empresa: Empresa) -> None: ...
    def listar_filiais(self, *, tenant_id: UUID, empresa_id: UUID) -> list[Filial]: ...
    def salvar_filial(self, filial: Filial) -> None: ...


class ImpostoRepository(Protocol):
    def listar(
        self,
        *,
        tenant_id: UUID,
        tipo: TipoImposto | None = None,
        filial_id: UUID | None = None,
    ) -> list[Imposto]: ...
    def salvar_nova_linha(self, imposto: Imposto) -> None: ...
    def encerrar_vigencia(
        self, *, tenant_id: UUID, imposto_id: UUID, fim: datetime
    ) -> None: ...


class SerieDocumentoRepository(Protocol):
    def obter(
        self, *, tenant_id: UUID, tipo: TipoDocumento, prefixo: str, filial_id: UUID | None
    ) -> SerieDocumento | None: ...
    def obter_por_id(
        self, *, tenant_id: UUID, serie_id: UUID
    ) -> SerieDocumento | None: ...
    def salvar(self, serie: SerieDocumento) -> None: ...
    def reservar_numero(
        self, *, tenant_id: UUID, serie_id: UUID, ano: int | None = None
    ) -> ReservaNumeroDocumento:
        """Reserva e retorna o próximo número atômico (resultado estruturado).

        Gap-less (fatura/certificado): reserva-TTL + consecutividade densa —
        `reserva_id` preenchido (confirmação one-shot endereça por ele).
        Buracos-aceitos (demais): UPDATE atômico (buraco por rollback aceito) —
        `reserva_id=None` (não há reserva a confirmar).
        """
        ...

    def confirmar_numero(self, *, tenant_id: UUID, reserva_id: UUID) -> bool:
        """One-shot do gap-less, DENTRO da transação do emissor (molde M8).

        Endereça pela PK da reserva — NUNCA por (serie, ano, sequencial), que
        após expiração+reuso apontaria para reserva viva de fluxo alheio.
        False se expirada/já confirmada/inexistente (caller re-reserva).
        """
        ...

    def liberar_expirados(
        self, *, tenant_id: UUID, serie_id: UUID, ano: int | None = None
    ) -> int:
        """Remove reservas não-confirmadas vencidas (devolve número à sequência).
        Retorna a quantidade liberada."""
        ...
