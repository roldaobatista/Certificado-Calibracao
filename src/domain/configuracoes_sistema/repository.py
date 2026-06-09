"""Protocols de repositório do domínio `configuracoes-sistema` (Fatia 1a — T-CFG-015).

Interfaces (sem Django). Implementação Django na infra (Fatia 1b).
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .entities import Empresa, Filial, Imposto, SerieDocumento


class EmpresaRepository(Protocol):
    def obter(self, *, tenant_id: UUID) -> Empresa | None: ...
    def salvar(self, empresa: Empresa) -> None: ...
    def listar_filiais(self, *, tenant_id: UUID, empresa_id: UUID) -> list[Filial]: ...
    def salvar_filial(self, filial: Filial) -> None: ...


class ImpostoRepository(Protocol):
    def listar(
        self, *, tenant_id: UUID, tipo: object | None = None, filial_id: UUID | None = None
    ) -> list[Imposto]: ...
    def salvar_nova_linha(self, imposto: Imposto) -> None: ...
    def encerrar_vigencia(self, *, tenant_id: UUID, imposto_id: UUID, fim: object) -> None: ...


class SerieDocumentoRepository(Protocol):
    def obter(
        self, *, tenant_id: UUID, tipo: object, prefixo: str, filial_id: UUID | None
    ) -> SerieDocumento | None: ...
    def salvar(self, serie: SerieDocumento) -> None: ...
    def reservar_numero(
        self, *, tenant_id: UUID, serie_id: UUID, ano: int | None = None
    ) -> int:
        """Reserva e retorna o próximo número atômico.

        Gap-less (fatura/certificado): reserva-TTL + consecutividade densa.
        Buracos-aceitos (demais): UPDATE atômico (buraco por rollback aceito).
        """
        ...
