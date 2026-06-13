"""Protocols de repositório do módulo `precificacao` (T-PRC-015 — ADR-0007).

Tipos reais nas assinaturas (lição M1 — zero `object`/`Any` de escape).
Adapters Django na Fatia 1b. Todos runtime_checkable para inspecção em testes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import (
    FaixaAprovacaoDesconto,
    ParametrosPrecificacaoTenant,
    PedidoAprovacaoDesconto,
    RegraFormacaoPreco,
    VinculoTabelaPrecoCliente,
)
from .enums import EstadoPedido


@runtime_checkable
class RegraRepository(Protocol):
    """Repositório de `RegraFormacaoPreco` (WORM — D-PRC-7)."""

    def obter(self, *, tenant_id: UUID, regra_id: UUID) -> RegraFormacaoPreco | None: ...

    def obter_vigente(
        self, *, tenant_id: UUID, item_id: UUID, em: datetime
    ) -> RegraFormacaoPreco | None:
        """Retorna a regra vigente em `em` para o item; None se ausente.

        Revogada NUNCA resolve (molde versão vigente PPS — lição M2).
        """
        ...

    def listar_por_item(
        self, *, tenant_id: UUID, item_id: UUID
    ) -> list[RegraFormacaoPreco]: ...

    def travar_item(self, *, tenant_id: UUID, item_id: UUID) -> None:
        """Advisory lock namespace 880_404 por (tenant, item) — Fatia 1b.

        Serializa publicar_regra e revogar_regra para o mesmo item.
        Fake implementa no-op.
        """
        ...

    def salvar(self, regra: RegraFormacaoPreco) -> None: ...

    def encerrar_vigencia(
        self, *, tenant_id: UUID, regra_id: UUID, fim: datetime
    ) -> None:
        """One-shot NULL→data; sem vigência aberta → RuntimeError (→ 409)."""
        ...

    def revogar(
        self, *, tenant_id: UUID, regra_id: UUID, revogado_em: datetime, motivo: str
    ) -> None:
        """One-shot; já revogada/inexistente → RuntimeError (→ 409)."""
        ...


@runtime_checkable
class FaixaRepository(Protocol):
    """Repositório de `FaixaAprovacaoDesconto` — replace-all atômico (D-PRC-3)."""

    def listar(self, *, tenant_id: UUID) -> list[FaixaAprovacaoDesconto]: ...

    def substituir_todas(
        self,
        *,
        tenant_id: UUID,
        faixas: list[FaixaAprovacaoDesconto],
        criado_por: UUID,
    ) -> None:
        """Replace-all atômico: valida CONJUNTO 0..100 antes de persistir (TL-PRC-16).

        Advisory lock no adapter: garante que dois replace-all concorrentes
        não intercalam (namespace 880_404, por tenant).
        """
        ...


@runtime_checkable
class PedidoRepository(Protocol):
    """Repositório de `PedidoAprovacaoDesconto` (WORM one-shot — D-PRC-14)."""

    def obter(
        self, *, tenant_id: UUID, pedido_id: UUID
    ) -> PedidoAprovacaoDesconto | None: ...

    def listar_pendentes(
        self, *, tenant_id: UUID
    ) -> list[PedidoAprovacaoDesconto]:
        """Lista pedidos no estado SOLICITADO para o tenant."""
        ...

    def salvar(self, pedido: PedidoAprovacaoDesconto) -> None: ...

    def decidir(
        self,
        *,
        tenant_id: UUID,
        pedido_id: UUID,
        estado: EstadoPedido,
        decisor_id: UUID,
        justificativa_hash: str,
        decidido_em: datetime,
    ) -> None:
        """One-shot SOLICITADO→APROVADO|NEGADO; outro estado → RuntimeError (→ 409).

        Grava justificativa_hash no campo WORM (D-PRC-15 / INV-PRC-APROVACAO-ONE-SHOT).
        """
        ...


@runtime_checkable
class VinculoTabelaRepository(Protocol):
    """Repositório de `VinculoTabelaPrecoCliente` (D-PRC-12)."""

    def obter_por_cliente(
        self, *, tenant_id: UUID, cliente_id: UUID, em: datetime
    ) -> VinculoTabelaPrecoCliente | None:
        """Retorna vínculo vigente em `em` para o cliente; None se ausente."""
        ...

    def salvar(self, vinculo: VinculoTabelaPrecoCliente) -> None: ...

    def revogar(
        self, *, tenant_id: UUID, vinculo_id: UUID, revogado_em: datetime, motivo: str
    ) -> None:
        """One-shot de revogação (consumer de Cliente.Anonimizado — ADR-0032)."""
        ...


@runtime_checkable
class ParametrosRepository(Protocol):
    """Repositório de `ParametrosPrecificacaoTenant` — singleton versionado por tenant."""

    def obter_vigentes(
        self, *, tenant_id: UUID
    ) -> ParametrosPrecificacaoTenant | None:
        """Retorna os parâmetros vigentes; None se tenant nunca configurou."""
        ...

    def salvar(self, parametros: ParametrosPrecificacaoTenant) -> None: ...
