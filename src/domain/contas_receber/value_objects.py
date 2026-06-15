"""Value Objects do domínio contas-receber (Fatia 1a — T-CR-015).

Todos `frozen + slots` (imutáveis). Molde `src/domain/fiscal/value_objects.py`.
`Dinheiro` e `ReferenciaPIIAnonimizavel` são reutilizados de `shared` (não criados aqui).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from src.domain.shared.value_objects import Dinheiro


@dataclass(frozen=True, slots=True)
class RegraJurosMulta:
    """Regra de juros e multa aplicada ao cálculo de valor atualizado (D-CR-4).

    `juros_ao_mes_pct` — juros mensais em percentual (default 1.0 = 1% a.m.).
    `multa_pct`        — multa one-shot no D+1 em percentual (default 2.0 = 2%).

    Persistida como referência no `Titulo` (`regra_juros_id`) — o valor calculado
    NÃO é persistido (INV-026); só o snapshot no pagamento é materializado (M-FIN-002).
    """

    juros_ao_mes_pct: Decimal = Decimal("1.0")  # 1% a.m.
    multa_pct: Decimal = Decimal("2.0")  # 2% one-shot D+1

    def __post_init__(self) -> None:
        if self.juros_ao_mes_pct < 0:
            raise ValueError(
                f"RegraJurosMulta.juros_ao_mes_pct não pode ser negativo: {self.juros_ao_mes_pct}"
            )
        if self.multa_pct < 0:
            raise ValueError(f"RegraJurosMulta.multa_pct não pode ser negativo: {self.multa_pct}")


@dataclass(frozen=True, slots=True)
class CobrancaCriada:
    """Resultado da porta `PaymentGatewayProvider.criar_cobranca` (D-CR-7).

    Campos opcionais dependem do `MeioCobranca`:
      - boleto: `linha_digitavel` presente.
      - pix/pix_recorrente: `qr_code` e/ou `tx_id` presentes.
    """

    gateway_id: str  # id no gateway (ex: "MOCK-a1b2c3d4")
    linha_digitavel: str | None = None
    qr_code: str | None = None
    tx_id: str | None = None
    url_pagamento: str | None = None
    raw_response: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CobrancaCancelada:
    """Resultado da porta `PaymentGatewayProvider.cancelar_cobranca` (D-CR-7)."""

    gateway_id: str
    cancelado_em: datetime
    raw_response: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecorrenciaCriada:
    """Resultado de `PaymentGatewayProvider.criar_recorrencia` (US-CR-002 / D-CR-7).

    Wave A emite só o 1º título; os subsequentes = Wave B (TL-CR-09).
    `convenio_id` — id do convênio PIX recorrente no gateway.
    """

    gateway_id: str
    convenio_id: str  # convenio_pix_id a salvar no Titulo
    primeiro_vencimento: date
    raw_response: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EventoNormalizado:
    """Resultado de `PaymentGatewayProvider.verificar_webhook` (D-CR-8).

    Payload normalizado do gateway após validação HMAC. O handler de webhook
    extrai SÓ os campos que `Pagamento` precisa — NÃO persiste PII do pagador
    (D-CR-19 / INV-CR-WEBHOOK-PAYLOAD-MINIMO).

    `gateway_event_id` — id único do evento no gateway (idempotência dupla R10).
    `valor_pago`       — valor efetivamente pago em centavos.
    `data_pagamento`   — data UTC do pagamento.
    `titulo_gateway_id` — `gateway_externo_id` do título para lookup.
    """

    gateway_event_id: str
    titulo_gateway_id: str  # liga ao Titulo via gateway_externo_id
    valor_pago: Dinheiro
    data_pagamento: date
    raw_response: Mapping[str, object] = field(default_factory=dict)
