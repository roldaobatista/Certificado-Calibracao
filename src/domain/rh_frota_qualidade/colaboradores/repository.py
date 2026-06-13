"""Protocols de repositório do módulo `colaboradores` (T-COL-015 — ADR-0007).

Tipos reais nas assinaturas (lição M1 — zero `object`/`Any` de escape).
Adapters Django na Fatia 1b (`src/infrastructure/colaboradores/`).
Todos runtime_checkable para inspeção em testes.

Refs: spec §4/§6; D-COL-1/3/4/5; ADR-0007.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import (
    CatalogoHabilidade,
    Colaborador,
    Documento,
    Habilidade,
    PapelColaboradorAtribuido,
)
from .enums import PapelColaborador


@runtime_checkable
class ColaboradorRepository(Protocol):
    """Repositório do agregado raiz `Colaborador` (D-COL-3 / ADR-0007)."""

    def obter(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        incluir_deletados: bool = False,
    ) -> Colaborador | None:
        """Retorna o colaborador; None se inexistente.

        Soft-deleted retorna apenas se `incluir_deletados=True`.
        """
        ...

    def obter_por_cpf(
        self,
        *,
        tenant_id: UUID,
        cpf_value: str,
    ) -> Colaborador | None:
        """Retorna colaborador ativo com o CPF; None se inexistente.

        Usado pelo use case de cadastro para verificar duplicidade
        (INV-COL-CPF). Busca apenas colaboradores não-deletados.
        """
        ...

    def listar_ativos(
        self,
        *,
        tenant_id: UUID,
        papel: PapelColaborador | None = None,
    ) -> list[Colaborador]:
        """Lista colaboradores ativos, opcionalmente filtrados por papel.

        Alimenta `/elegiveis` (manager `ativos` — data_desligamento IS NULL).
        """
        ...

    def salvar(self, colaborador: Colaborador) -> None:
        """Insere ou atualiza o colaborador (upsert por id)."""
        ...

    def desligar(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        data_desligamento: date,
        motivo_desligamento: str,
    ) -> None:
        """Registra desligamento: preenche data_desligamento + motivo.

        Chamado pelo use case de desligamento (D-COL-3 / D-COL-10).
        O cascade de revogação de papéis ocorre no use case, não aqui.
        """
        ...

    def soft_delete(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        deletado_em: datetime,
        deletado_por_usuario_id: UUID,
        deletado_motivo: str,
    ) -> None:
        """Soft-delete Padrão C (D-COL-3): preenche deletado_em + auditoria."""
        ...


@runtime_checkable
class PapelRepository(Protocol):
    """Repositório de `PapelColaboradorAtribuido` (D-COL-4 / ADR-0007)."""

    def listar_por_colaborador(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> list[PapelColaboradorAtribuido]:
        """Retorna todos os papéis do colaborador (incluindo revogados).

        Revogados mantidos para audit (D-COL-4 / INV-001).
        """
        ...

    def existe_dono_ativo(self, *, tenant_id: UUID) -> bool:
        """True se já existe papel DONO ativo no tenant.

        WHERE papel='DONO' AND data_fim IS NULL AND revogado_em IS NULL
        (INV-COL-DONO-UNICO / D-COL-4).
        """
        ...

    def salvar(self, papel: PapelColaboradorAtribuido) -> None:
        """Insere um novo papel atribuído."""
        ...

    def revogar(
        self,
        *,
        tenant_id: UUID,
        papel_id: UUID,
        revogado_em: datetime,
    ) -> None:
        """Revogação: seta revogado_em; nunca apaga a linha (audit)."""
        ...

    def revogar_todos_ativos(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        revogado_em: datetime,
    ) -> int:
        """Revoga todos os papéis ativos do colaborador.

        Chamado no cascade de desligamento (INV-COL-DESLIGAMENTO-CASCADE).
        Retorna a quantidade de papéis revogados.
        """
        ...

    def travar_dono_por_tenant(self, *, tenant_id: UUID) -> None:
        """Advisory lock para troca de DONO (namespace 880_405 — ADR-0065).

        Serializa atribuições concorrentes de DONO para o mesmo tenant.
        Fake implementa no-op.
        """
        ...


@runtime_checkable
class HabilidadeRepository(Protocol):
    """Repositório de `Habilidade` (D-COL-5 / ADR-0007)."""

    def listar_por_colaborador(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> list[Habilidade]: ...

    def salvar(self, habilidade: Habilidade) -> None: ...

    def remover(
        self,
        *,
        tenant_id: UUID,
        habilidade_id: UUID,
    ) -> None: ...


@runtime_checkable
class DocumentoRepository(Protocol):
    """Repositório de `Documento` (D-COL-6 / ADR-0007)."""

    def listar_por_colaborador(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> list[Documento]: ...

    def salvar(self, documento: Documento) -> None: ...

    def remover(
        self,
        *,
        tenant_id: UUID,
        documento_id: UUID,
    ) -> None: ...


@runtime_checkable
class CatalogoHabilidadeRepository(Protocol):
    """Repositório de `CatalogoHabilidade` global read-only (D-COL-5 / TL-COL-10).

    Sem `tenant_id` — tabela global sem RLS (Fatia 1b).
    Escrita apenas via migration de seed (INSERT-só-seed — TL-COL-10).
    """

    def listar(self) -> list[CatalogoHabilidade]:
        """Lista todas as habilidades do catálogo global."""
        ...

    def obter_por_codigo(self, *, codigo: str) -> CatalogoHabilidade | None:
        """Busca por código; None se inexistente."""
        ...
