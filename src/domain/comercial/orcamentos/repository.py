"""Protocols de repositório do domínio Orçamentos — T-ORC-013.

Contratos puros (``typing.Protocol``); implementações concretas Django vivem em
``src/infrastructure/orcamentos/repositories.py``.

Molde: ``src/domain/comercial/clientes/repository.py``.

Zero imports Django / infrastructure.

Refs:
  D-ORC-2  — path aninhado comercial
  D-ORC-4  — ReferenciaPIIAnonimizavel
  D-ORC-7  — LinkPublico / token
  D-ORC-8  — VersaoOrcamento imutável
  D-ORC-13 — TemplateRepository
  D-ORC-15 — AnaliseCriticaOrcamento WORM
  D-ORC-18 — numeração gap-less (SerieDocumento — infra resolve)
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.comercial.orcamentos.entities import (
    AnaliseCriticaOrcamento,
    Aprovacao,
    ItemOrcamento,
    LinkPublico,
    Orcamento,
    Template,
    VersaoOrcamento,
)
from src.domain.comercial.orcamentos.enums import EstadoOrcamento

# =====================================================================
# ORCAMENTO REPOSITORY
# =====================================================================


@runtime_checkable
class OrcamentoRepository(Protocol):
    """Contrato de persistência do agregado Orçamento.

    Todos os métodos de escrita devem ser chamados DENTRO de ``transaction.atomic``
    pelo use case caller. Repositório não gerencia transação.
    """

    def get_by_id(
        self,
        orcamento_id: UUID,
        *,
        tenant_id: UUID,
    ) -> Orcamento | None:
        """Busca por id dentro do tenant (RLS garante, mas tenant_id é explícito)."""
        ...

    def salvar(self, orcamento: Orcamento) -> Orcamento:
        """INSERT ou UPDATE do agregado raiz."""
        ...

    def listar(
        self,
        *,
        tenant_id: UUID,
        estado: EstadoOrcamento | None = None,
        cliente_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Orcamento]:
        """Listagem paginada com filtros opcionais."""
        ...

    def salvar_versao(self, versao: VersaoOrcamento) -> VersaoOrcamento:
        """INSERT de VersaoOrcamento (imutável pós-insert — trigger WORM)."""
        ...

    def get_versao_ativa(self, orcamento_id: UUID, *, tenant_id: UUID) -> VersaoOrcamento | None:
        """Retorna a última versão não revogada do orçamento."""
        ...

    def congelar_versao(
        self,
        versao_id: UUID,
        *,
        tenant_id: UUID,
        snapshot: dict[str, object],
    ) -> VersaoOrcamento:
        """Congela o snapshot da versão corrente (UPDATE one-shot `{}` -> conteúdo).

        O trigger WORM (0003) permite preencher snapshot vazio uma única vez ao
        enviar (D-ORC-8); re-edição de snapshot já congelado é bloqueada no banco.
        """
        ...

    def salvar_item(self, item: ItemOrcamento) -> ItemOrcamento:
        """INSERT de ItemOrcamento numa versão."""
        ...

    def listar_itens_versao(self, versao_id: UUID, *, tenant_id: UUID) -> list[ItemOrcamento]:
        """Itens de uma versão específica, ordenados por sequencia."""
        ...

    def salvar_aprovacao(self, aprovacao: Aprovacao) -> Aprovacao:
        """INSERT de Aprovacao (WORM — trigger bloqueia UPDATE/DELETE)."""
        ...

    def salvar_analise_critica(self, analise: AnaliseCriticaOrcamento) -> AnaliseCriticaOrcamento:
        """INSERT de AnaliseCriticaOrcamento (WORM — trigger anti-mutação)."""
        ...

    def get_analise_critica(
        self, orcamento_id: UUID, *, tenant_id: UUID
    ) -> AnaliseCriticaOrcamento | None:
        """Retorna a análise crítica associada ao orçamento."""
        ...

    def salvar_link(self, link: LinkPublico) -> LinkPublico:
        """INSERT do LinkPublico (partial unique WHERE revogado_em IS NULL)."""
        ...

    def get_link_ativo(self, orcamento_id: UUID, *, tenant_id: UUID) -> LinkPublico | None:
        """Retorna link público ativo (revogado_em IS NULL), se existir."""
        ...

    def get_link_por_token(self, token: str) -> LinkPublico | None:
        """Busca por token opaco SEM RLS (resolve tenant — D-ORC-19).

        Necessário para o endpoint público (token resolve tenant antes do contexto).
        Implementação usa tabela de índice de token ou função SECURITY DEFINER.
        """
        ...

    def revogar_link(
        self,
        link_id: UUID,
        *,
        revogado_em: datetime,
        motivo: str,
    ) -> None:
        """Marca o link como revogado (não DELETE — soft-revoke)."""
        ...

    def atualizar_estado(
        self,
        orcamento_id: UUID,
        *,
        tenant_id: UUID,
        novo_estado: EstadoOrcamento,
    ) -> Orcamento:
        """Atualiza apenas o campo estado (idempotente — valida transição no use case)."""
        ...


# =====================================================================
# TEMPLATE REPOSITORY
# =====================================================================


@runtime_checkable
class TemplateRepository(Protocol):
    """Contrato de persistência de Templates de orçamento (D-ORC-13)."""

    def get_by_id(self, template_id: UUID, *, tenant_id: UUID) -> Template | None:
        """Busca por id (soft-delete retorna None se ``deletado_em`` preenchido)."""
        ...

    def salvar(self, template: Template) -> Template:
        """INSERT ou UPDATE do template."""
        ...

    def listar(
        self,
        *,
        tenant_id: UUID,
        incluir_deletados: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Template]:
        """Listagem paginada."""
        ...

    def soft_delete(
        self,
        template_id: UUID,
        *,
        tenant_id: UUID,
        deletado_por: UUID,
        deletado_em: datetime,
    ) -> Template:
        """Soft-delete (Padrão C): preenche ``deletado_em`` + ``deletado_por``."""
        ...
