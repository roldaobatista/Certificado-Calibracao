"""Porta `PaymentGatewayProvider` e `TituloRepository` (Fatia 1a — T-CR-015).

INV-FIS-003 / D-CR-7: domínio/use case NUNCA importam SDK de gateway; toda emissão
passa por este Protocol. O use case sempre recebe um `PaymentGatewayProvider` injetado
— agnóstico de qual implementação (mock no domínio, adapter Asaas na infra).

Import de SDK confinado a `infrastructure/contas_receber/` (hook
`cr-provider-import-fronteira-check.sh`, molde `fiscal-provider-import-fronteira-check`).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
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
    """Repositório de `Titulo` — porta de persistência (implementado na Fatia 1b).

    Retorna entidades de domínio puras (`Titulo`, `Pagamento`). A implementação
    concreta `DjangoTituloRepository` vive em `infrastructure/contas_receber/`.
    """

    def obter_por_id(self, titulo_id: UUID, tenant_id: UUID) -> Titulo:
        """Levanta `KeyError` se não encontrado (cross-tenant 404 via RLS)."""
        ...

    def salvar(self, titulo: Titulo) -> None:
        """Persiste ou atualiza o título (OCC via `revision`)."""
        ...

    def listar_pagamentos(self, titulo_id: UUID) -> list[Pagamento]:
        """Lista pagamentos do título (INSERT-only — nunca retorna deletados)."""
        ...

    def obter_por_gateway_id(self, gateway_id: str, tenant_id: UUID) -> Titulo | None:
        """Lookup por `gateway_externo_id` (webhook — D-CR-8). Retorna None se não encontrado."""
        ...

    def iter_vencidos_por_tenant(self, tenant_id: UUID) -> Iterator[Titulo]:
        """Itera títulos vencidos para o adapter de inadimplência (D-CR-9)."""
        ...
