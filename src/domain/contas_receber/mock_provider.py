"""`MockPaymentGatewayProvider` — implementação determinística da porta (Fatia 1a, T-CR-015).

Vive no DOMÍNIO (D-CR-7): sem I/O, sem SDK, sem rede; é a implementação de referência
do Protocol `PaymentGatewayProvider`. Molde: `src/domain/fiscal/mock_provider.py`.

4 modos (`ModoMock`):
  - `always_confirm`      → `CobrancaCriada` imediata com `gateway_id` determinístico.
  - `pending_then_confirm` → 1ª `criar_cobranca` devolve cobrança com sufixo `-PENDING`;
                             `verificar_webhook` subsequente devolve `EventoNormalizado`
                             com confirmação. Simula PIX assíncrono.
  - `always_reject`       → levanta `GatewayIndisponivel` (fornecedor recusou).
  - `network_timeout`     → levanta `GatewayIndisponivel` com mensagem de timeout.

`gateway_id` DETERMINÍSTICO por dados NÃO-PII (`titulo_id` + `meio` + `vencimento`):
  - Não inclui `cliente_id`/`cpf_cnpj`/nome do pagador.
  - Usa `zlib.crc32` (não-cripto, suficiente para id estável de mock — molde fiscal).
  - Mesmo payload → mesmo id → testes reproduzíveis.

`verificar_webhook` no mock aceita qualquer `signature` não-vazia (HMAC real = GATE-CR-ASAAS).
Signature vazia → levanta `WebhookHMACInvalido` (testa o caminho 401).
"""

from __future__ import annotations

import zlib
from datetime import UTC, date, datetime
from enum import Enum
from uuid import UUID

from src.domain.shared.value_objects import Dinheiro

from .erros import GatewayIndisponivel, WebhookHMACInvalido
from .value_objects import (
    CobrancaCancelada,
    CobrancaCriada,
    EventoNormalizado,
    RecorrenciaCriada,
)


class ModoMock(str, Enum):
    """Modos determinísticos do mock de gateway."""

    ALWAYS_CONFIRM = "always_confirm"
    PENDING_THEN_CONFIRM = "pending_then_confirm"
    ALWAYS_REJECT = "always_reject"
    NETWORK_TIMEOUT = "network_timeout"


def _gateway_id_deterministico(titulo_id: UUID, meio: str, vencimento: date) -> str:
    """id estável derivado de campos NÃO-PII (sem cliente/CPF/nome).

    `zlib.crc32` (não-cripto) é suficiente para id de mock — evita qualquer
    ambiguidade com hash de PII (molde `_id_deterministico` do fiscal).
    """
    base = f"{titulo_id}|{meio}|{vencimento.isoformat()}"
    crc = zlib.crc32(base.encode("utf-8")) & 0xFFFFFFFF
    return f"MOCK-{crc:08x}"


class MockPaymentGatewayProvider:
    """Provider de teste — satisfaz `PaymentGatewayProvider` estruturalmente."""

    def __init__(self, modo: ModoMock = ModoMock.ALWAYS_CONFIRM) -> None:
        self.modo = modo
        # Cobra criadas em modo pending_then_confirm (para simular webhook)
        self._pendentes: dict[str, tuple[Dinheiro, date]] = {}

    def criar_cobranca(
        self,
        titulo_id: UUID,
        valor: Dinheiro,
        vencimento: date,
        meio: str,
        metadata: dict[str, object] | None = None,
    ) -> CobrancaCriada:
        """Cria cobrança determinística. Levanta `GatewayIndisponivel` em reject/timeout."""
        if self.modo is ModoMock.NETWORK_TIMEOUT:
            raise GatewayIndisponivel("mock: timeout de rede simulado")

        if self.modo is ModoMock.ALWAYS_REJECT:
            raise GatewayIndisponivel("mock: rejeição determinística pelo gateway")

        gateway_id = _gateway_id_deterministico(titulo_id, meio, vencimento)

        if self.modo is ModoMock.PENDING_THEN_CONFIRM:
            self._pendentes[gateway_id] = (valor, vencimento)
            return CobrancaCriada(
                gateway_id=gateway_id + "-PENDING",
                qr_code=f"mock://qr/{gateway_id}",
                tx_id=f"mock-tx-{gateway_id[-8:]}",
                raw_response={"mock_modo": self.modo.value, "status": "PENDING"},
            )

        # ALWAYS_CONFIRM
        if meio == "boleto":
            return CobrancaCriada(
                gateway_id=gateway_id,
                linha_digitavel=f"1234.5678 9012.345678 90123.456789 {gateway_id[-8:]} 1234",
                url_pagamento=f"mock://boleto/{gateway_id}",
                raw_response={"mock_modo": self.modo.value},
            )
        # pix / cartao
        return CobrancaCriada(
            gateway_id=gateway_id,
            qr_code=f"mock://qr/{gateway_id}",
            tx_id=f"mock-tx-{gateway_id[-8:]}",
            url_pagamento=f"mock://pix/{gateway_id}",
            raw_response={"mock_modo": self.modo.value},
        )

    def cancelar_cobranca(self, gateway_id: str) -> CobrancaCancelada:
        """Cancela cobrança (aceita qualquer id no mock)."""
        self._pendentes.pop(gateway_id.removesuffix("-PENDING"), None)
        return CobrancaCancelada(
            gateway_id=gateway_id,
            cancelado_em=datetime.now(UTC),
            raw_response={"mock_cancelamento": True},
        )

    def criar_recorrencia(
        self,
        titulo_id: UUID,
        convenio_pix_id: str,
        valor: Dinheiro,
        primeiro_vencimento: date,
        metadata: dict[str, object] | None = None,
    ) -> RecorrenciaCriada:
        """Cria convênio PIX recorrente (emite só o 1º título — TL-CR-09)."""
        if self.modo in (ModoMock.NETWORK_TIMEOUT, ModoMock.ALWAYS_REJECT):
            raise GatewayIndisponivel(f"mock: {self.modo.value} em criar_recorrencia")

        gateway_id = _gateway_id_deterministico(titulo_id, "pix_recorrente", primeiro_vencimento)
        return RecorrenciaCriada(
            gateway_id=gateway_id,
            convenio_id=f"{convenio_pix_id}-{gateway_id[-8:]}",
            primeiro_vencimento=primeiro_vencimento,
            raw_response={"mock_modo": self.modo.value},
        )

    def cancelar_recorrencia(self, gateway_id: str) -> CobrancaCancelada:
        """Cancela convênio recorrente."""
        return CobrancaCancelada(
            gateway_id=gateway_id,
            cancelado_em=datetime.now(UTC),
            raw_response={"mock_cancelamento_recorrencia": True},
        )

    def verificar_webhook(self, payload: bytes, signature: str) -> EventoNormalizado:
        """Valida HMAC mock e devolve evento normalizado (D-CR-8).

        Mock aceita qualquer `signature` não-vazia.
        `signature` vazia → levanta `WebhookHMACInvalido` (testa caminho 401).
        Lê `gateway_event_id` e `titulo_gateway_id` de `payload` decodificado como
        "gateway_event_id|titulo_gateway_id|centavos|YYYY-MM-DD".
        """
        if not signature:
            raise WebhookHMACInvalido("mock: signature vazia — HMAC inválido")

        # Formato do payload mock: "event_id|titulo_gw_id|centavos|data_iso"
        try:
            partes = payload.decode("utf-8").split("|")
            gateway_event_id = partes[0]
            titulo_gateway_id = partes[1]
            centavos = int(partes[2])
            data_pagamento = date.fromisoformat(partes[3])
        except (IndexError, ValueError) as exc:
            raise WebhookHMACInvalido(f"mock: payload malformado: {payload!r}") from exc

        return EventoNormalizado(
            gateway_event_id=gateway_event_id,
            titulo_gateway_id=titulo_gateway_id,
            valor_pago=Dinheiro(centavos),
            data_pagamento=data_pagamento,
            raw_response={"mock_webhook": True},
        )
