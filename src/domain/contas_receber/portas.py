"""Porta `PaymentGatewayProvider` e `TituloRepository` (Fatia 1a — T-CR-015).

INV-FIS-003 / D-CR-7: domínio/use case NUNCA importam SDK de gateway; toda emissão
passa por este Protocol. O use case sempre recebe um `PaymentGatewayProvider` injetado
— agnóstico de qual implementação (mock no domínio, adapter Asaas na infra).

Import de SDK confinado a `infrastructure/contas_receber/` (hook
`cr-provider-import-fronteira-check.sh`, molde `fiscal-provider-import-fronteira-check`).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.shared.value_objects import Dinheiro

from .entities import Pagamento, Titulo
from .value_objects import (
    CobrancaCancelada,
    CobrancaCriada,
    EventoNormalizado,
    RecorrenciaCriada,
)


@runtime_checkable
class PaymentGatewayProvider(Protocol):
    """Porta de gateway de pagamento — agnóstica de fornecedor (D-CR-7 / ADR-0050).

    Operações Wave A (Mock + adapter Asaas = GATE-CR-ASAAS):
      - `criar_cobranca`       → boleto / PIX avulso.
      - `cancelar_cobranca`    → cancela cobrança no gateway.
      - `criar_recorrencia`    → convênio PIX recorrente (emite só o 1º título — TL-CR-09).
      - `cancelar_recorrencia` → cancela convênio.
      - `verificar_webhook`    → valida HMAC + normaliza payload (D-CR-8 / INV-FIN-GW-001).

    `criar_cobranca` pode levantar `GatewayIndisponivel` (transporte — D-CR-7):
    nenhum `Titulo` é persistido; aplicação faz 503 + publica `gateway_indisponivel`.
    """

    def criar_cobranca(
        self,
        titulo_id: UUID,
        valor: Dinheiro,
        vencimento: date,
        meio: str,
        metadata: dict[str, object] | None = None,
    ) -> CobrancaCriada:
        """Emite cobrança (boleto ou PIX avulso). Levanta `GatewayIndisponivel` em timeout."""
        ...

    def cancelar_cobranca(self, gateway_id: str) -> CobrancaCancelada:
        """Cancela cobrança existente no gateway."""
        ...

    def criar_recorrencia(
        self,
        titulo_id: UUID,
        convenio_pix_id: str,
        valor: Dinheiro,
        primeiro_vencimento: date,
        metadata: dict[str, object] | None = None,
    ) -> RecorrenciaCriada:
        """Registra convênio PIX recorrente e emite o 1º título (TL-CR-09)."""
        ...

    def cancelar_recorrencia(self, gateway_id: str) -> CobrancaCancelada:
        """Cancela convênio recorrente no gateway."""
        ...

    def verificar_webhook(self, payload: bytes, signature: str) -> EventoNormalizado:
        """Valida HMAC do payload e devolve evento normalizado (D-CR-8).

        Levanta `WebhookHMACInvalido` se assinatura inválida (→ 401 + incidente).
        NÃO extrai PII do pagador além do que `Pagamento` precisa (D-CR-19).
        """
        ...


@runtime_checkable
class TituloRepository(Protocol):
    """Repositório de `Titulo` — porta de persistência (contrato consumido pelos use cases).

    Retorna entidades de domínio puras (`Titulo`/`Pagamento`). A implementação concreta
    `DjangoTituloRepository` vive em `infrastructure/contas_receber/`. As assinaturas abaixo
    são o contrato real reconciliado na Fatia 2a (keyword-only `tenant_id` — RLS por escopo).
    Métodos de 2b/3 (override, recorrência, vencidos) entram quando suas fatias forem codadas.
    """

    # --- Titulo ---
    def obter_por_id(self, *, tenant_id: UUID, titulo_id: UUID) -> Titulo | None:
        """Retorna o título ou `None` (cross-tenant → None via RLS → 404 anti-oráculo)."""
        ...

    def salvar_novo_titulo(self, titulo: Titulo) -> None:
        """Persiste um título novo (INSERT)."""
        ...

    def atualizar_titulo(self, *, tenant_id: UUID, titulo: Titulo) -> None:
        """Transição de estado + campos mutáveis (bump de `revision`; trigger WORM enforça)."""
        ...

    def atualizar_titulo_cancelado(
        self, *, tenant_id: UUID, titulo: Titulo, cancelado_em: datetime
    ) -> None:
        """Cancela: estado=cancelado + `cancelado_em` one-shot (trigger 0003 enforça)."""
        ...

    def existe_titulo_ativo_para_os(self, *, tenant_id: UUID, os_id: UUID) -> bool:
        """Título ativo (não cancelado) para a OS — INV-CR-OS-TITULO-UNICO (auto-fatura, Fatia 3)."""
        ...

    def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        estado: str | None = None,
        cliente_atual_id: UUID | None = None,
    ) -> list[Titulo]:
        """Lista títulos do tenant com filtros opcionais (REST list)."""
        ...

    # --- Pagamento ---
    def salvar_pagamento(self, *, tenant_id: UUID, pagamento: Pagamento) -> None:
        """Persiste um pagamento (INSERT-only — WORM)."""
        ...

    def listar_pagamentos(self, *, tenant_id: UUID, titulo_id: UUID) -> list[Pagamento]:
        """Lista pagamentos do título (INSERT-only — nunca retorna deletados)."""
        ...

    def existe_gateway_event(self, *, tenant_id: UUID, gateway_event_id: str) -> bool:
        """Idempotência de webhook por `gateway_event_id` (INV-FIN-GW-001 — Fatia 2b)."""
        ...
