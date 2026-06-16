"""Use case: processar webhook de pagamento de gateway (Fatia 2b — T-CR-033).

Baixa automática via webhook do gateway externo (US-CR-003 / D-CR-8).

Idempotência DUPLA (INV-FIN-GW-001 / R10):
  (a) `repo.existe_gateway_event(gateway_event_id)` → replay exato → no-op (200).
  (b) Título já em estado `pago` → no-op (200 sem re-gravar Pagamento).

HMAC:
  `provider.verificar_webhook(payload, signature)` → levanta `WebhookHMACInvalido` (→ 401).
  NÃO capturamos — a VIEW captura e responde 401 + publica incidente.

Clean arch: NÃO importa DRF. NÃO publica evento — a VIEW publica dentro do mesmo
`transaction.atomic`. O use case retorna `ProcessarWebhookOutput` com resultado
normalizado.

Anti-oráculo (D-CR-8): o HMAC é validado ANTES de qualquer consulta ao banco de dados
de tenant. A VIEW deve resolver o tenant via SECURITY DEFINER ANTES de chamar este
use case. Se `titulo_gateway_id` não for encontrado após HMAC válido, a VIEW responde
401 igual ao HMAC inválido (não vaza existência de gateway_id).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.contas_receber.entities import Pagamento
from src.domain.contas_receber.enums import EstadoTitulo, OrigemPagamento
from src.domain.contas_receber.erros import TituloNaoEncontrado
from src.domain.contas_receber.portas import PaymentGatewayProvider, TituloRepository
from src.domain.contas_receber.transicoes import validar_transicao
from src.domain.contas_receber.value_objects import EventoNormalizado


@dataclass(frozen=True, slots=True)
class ProcessarWebhookInput:
    """Payload bruto do webhook — provider valida HMAC e normaliza."""

    tenant_id: UUID
    payload_bytes: bytes  # corpo bruto do request HTTP
    signature: str  # header de assinatura do gateway


@dataclass(frozen=True, slots=True)
class ProcessarWebhookOutput:
    """Resultado da baixa via webhook."""

    evento: EventoNormalizado
    pagamento: Pagamento | None  # None se replay/já pago (idempotência)
    novo_estado: EstadoTitulo | None
    ja_processado: bool  # True = replay ou título já pago → no-op


def processar_webhook_pagamento(
    inp: ProcessarWebhookInput,
    *,
    repo: TituloRepository,
    provider: PaymentGatewayProvider,
) -> ProcessarWebhookOutput:
    """Processa webhook de baixa automática.

    Fluxo:
    1. Valida HMAC via `provider.verificar_webhook` — levanta `WebhookHMACInvalido` se inválido.
    2. Idempotência (a): já existe `gateway_event_id` → retorna `ja_processado=True` (no-op).
    3. Carrega título pelo `titulo_gateway_id` (gateway_externo_id); se não encontrado, propaga
       `TituloNaoEncontrado` — a VIEW trata como 401 anti-oráculo.
    4. Idempotência (b): título já `pago` → retorna `ja_processado=True` (no-op).
    5. Valida transição `→ pago`.
    6. Grava `Pagamento` + atualiza estado do título.
    7. Retorna resultado para a VIEW publicar os eventos e marcar gateway_event.

    NÃO executa `transaction.atomic` — a VIEW embrulha tudo em 1 tx (D-CR-8).
    """
    # 1. Valida HMAC — WebhookHMACInvalido propaga para a view (→ 401 + incidente).
    evento = provider.verificar_webhook(inp.payload_bytes, inp.signature)

    # 2. Idempotência (a): replay por gateway_event_id.
    if repo.existe_gateway_event(
        tenant_id=inp.tenant_id, gateway_event_id=evento.gateway_event_id
    ):
        return ProcessarWebhookOutput(
            evento=evento,
            pagamento=None,
            novo_estado=None,
            ja_processado=True,
        )

    # 3. Carrega título pelo gateway_externo_id.
    #    `repo.obter_titulo_por_gateway_id` é implementado no DjangoTituloRepository.
    #    Se não encontrado, a VIEW responde 401 (anti-oráculo D-CR-8 / R7).
    titulo = repo.obter_titulo_por_gateway_id(
        tenant_id=inp.tenant_id,
        gateway_externo_id=evento.titulo_gateway_id,
    )
    if titulo is None:
        raise TituloNaoEncontrado(
            f"Título com gateway_externo_id={evento.titulo_gateway_id!r} não encontrado."
        )

    # 4. Idempotência (b): título já pago.
    if titulo.estado == EstadoTitulo.PAGO:
        return ProcessarWebhookOutput(
            evento=evento,
            pagamento=None,
            novo_estado=EstadoTitulo.PAGO,
            ja_processado=True,
        )

    # 5. Valida transição → pago.
    validar_transicao(titulo.estado, EstadoTitulo.PAGO)

    # 6. Snapshot do valor atualizado no momento do pagamento (M-FIN-002).
    #    Wave A: sem regra de juros complexa no webhook — usa valor_original como snapshot.
    #    (O cálculo rico com juros/multa é para baixa manual; webhook é o valor que chegou.)
    snapshot_valor = titulo.valor_original

    agora = datetime.now(UTC)
    pagamento = Pagamento(
        pagamento_id=uuid4(),
        titulo_id=titulo.titulo_id,
        valor=evento.valor_pago,
        data=evento.data_pagamento,
        origem=OrigemPagamento.WEBHOOK_GATEWAY,
        valor_atualizado_snapshot_em_pagamento=snapshot_valor,
        criado_em=agora,
        gateway_event_id=evento.gateway_event_id,
    )

    # Grava pagamento (INSERT-only WORM). Savepoint isola a CORRIDA (P9 MÉDIO-1): se outro
    # webhook concorrente com o MESMO gateway_event_id já inseriu (UniqueConstraint
    # `uq_cr_pagamento_gateway_event`), o IntegrityError NÃO aborta a tx da view — vira replay
    # (no-op, sem 2º Pagamento WORM nem 2º evento publicado). Fecha o TOCTOU do check-then-act.
    from django.db import IntegrityError, transaction

    try:
        with transaction.atomic():
            repo.salvar_pagamento(tenant_id=inp.tenant_id, pagamento=pagamento)
    except IntegrityError:
        return ProcessarWebhookOutput(
            evento=evento,
            pagamento=None,
            novo_estado=None,
            ja_processado=True,
        )

    # Transiciona título → pago.
    from dataclasses import replace

    titulo_pago = replace(titulo, estado=EstadoTitulo.PAGO, data_baixa=evento.data_pagamento)
    repo.atualizar_titulo(tenant_id=inp.tenant_id, titulo=titulo_pago)

    return ProcessarWebhookOutput(
        evento=evento,
        pagamento=pagamento,
        novo_estado=EstadoTitulo.PAGO,
        ja_processado=False,
    )
