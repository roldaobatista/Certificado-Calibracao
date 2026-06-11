"""Protocols de repositório do catálogo (T-PPS-014 — ADR-0007).

Tipos reais nas assinaturas (lição M1 da 1ª passada P9 da frente #1 — zero
`object`/`Any` de escape). Adapters Django na Fatia 1b.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.domain.produtos_pecas_servicos.entities import (
    ImportacaoCatalogo,
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaImportacaoCatalogo,
    LinhaTabelaPreco,
    TabelaPreco,
)


class ItemCatalogoRepository(Protocol):
    def obter(self, *, tenant_id: UUID, item_id: UUID) -> ItemCatalogo | None: ...
    def obter_por_codigo(self, *, tenant_id: UUID, codigo_interno: str) -> ItemCatalogo | None: ...
    def listar(self, *, tenant_id: UUID, apenas_ativos: bool = False) -> list[ItemCatalogo]: ...
    def salvar(self, item: ItemCatalogo) -> None: ...
    def travar_item(self, *, tenant_id: UUID, item_id: UUID) -> None:
        """Serializa criar/corrigir versão por item (D-PPS-4 — advisory lock no
        adapter PG; Fakes implementam no-op)."""
        ...
    def listar_versoes(self, *, tenant_id: UUID, item_id: UUID) -> list[ItemCatalogoVersao]: ...
    def salvar_versao(self, versao: ItemCatalogoVersao) -> None: ...
    def encerrar_vigencia_versao(
        self, *, tenant_id: UUID, versao_id: UUID, fim: datetime
    ) -> None:
        """One-shot NULL→data; sem vigência aberta → RuntimeError (→ 409)."""
        ...

    def revogar_versao(self, *, tenant_id: UUID, versao_id: UUID, motivo: str) -> None:
        """One-shot; já revogada/inexistente → RuntimeError (→ 409)."""
        ...
    def listar_composicao(self, *, tenant_id: UUID, kit_item_id: UUID) -> list[KitComposicao]: ...
    def substituir_composicao(
        self, *, tenant_id: UUID, kit_item_id: UUID, composicao: list[KitComposicao]
    ) -> None: ...


class TabelaPrecoRepository(Protocol):
    def obter_padrao(self, *, tenant_id: UUID) -> TabelaPreco | None: ...
    def obter(self, *, tenant_id: UUID, tabela_id: UUID) -> TabelaPreco | None: ...
    def salvar(self, tabela: TabelaPreco) -> None: ...
    def travar_linha(self, *, tenant_id: UUID, tabela_id: UUID, item_id: UUID) -> None:
        """Serializa criar/corrigir linha por (tabela, item) — advisory no adapter."""
        ...
    def listar_linhas(
        self, *, tenant_id: UUID, tabela_id: UUID, item_id: UUID | None = None
    ) -> list[LinhaTabelaPreco]: ...
    def salvar_linha(self, linha: LinhaTabelaPreco) -> None: ...
    def encerrar_vigencia_linha(
        self, *, tenant_id: UUID, linha_id: UUID, fim: datetime
    ) -> None:
        """One-shot NULL→data; sem vigência aberta → RuntimeError (→ 409)."""
        ...

    def revogar_linha(self, *, tenant_id: UUID, linha_id: UUID, motivo: str) -> None:
        """One-shot; já revogada/inexistente → RuntimeError (→ 409)."""
        ...


class ImportacaoCatalogoRepository(Protocol):
    """Staging da importação CSV (US-CAT-004 — mutável, TTL 90d)."""

    def salvar_importacao(
        self, importacao: ImportacaoCatalogo, linhas: list[LinhaImportacaoCatalogo]
    ) -> None: ...
    def obter_importacao(
        self, *, tenant_id: UUID, importacao_id: UUID
    ) -> ImportacaoCatalogo | None: ...
    def listar_linhas(
        self, *, tenant_id: UUID, importacao_id: UUID
    ) -> list[LinhaImportacaoCatalogo]: ...
    def obter_linha(
        self, *, tenant_id: UUID, linha_id: UUID
    ) -> LinhaImportacaoCatalogo | None: ...
    def marcar_linha_aceita(
        self, *, tenant_id: UUID, linha_id: UUID, item_criado_id: UUID
    ) -> None:
        """One-shot VALIDADA→ACEITA; outro estado → RuntimeError (→ 409)."""
        ...

    def marcar_linha_rejeitada(self, *, tenant_id: UUID, linha_id: UUID, motivo: str) -> None:
        """One-shot VALIDADA→REJEITADA; outro estado → RuntimeError (→ 409)."""
        ...

    def eliminar_importacoes_anteriores_a(self, *, tenant_id: UUID, limite: datetime) -> int:
        """TTL 90d (ADV-PPS-06) — elimina lotes antigos (linhas em cascata);
        retorna quantos lotes saíram. Idempotente."""
        ...
