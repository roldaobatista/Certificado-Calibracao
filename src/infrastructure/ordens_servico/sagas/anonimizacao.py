"""T-OS-037 — Saga "Anonimizacao bloqueada por OS aberta".

Predicate `cliente_tem_os_aberta` (a expor em Fase 5 T-OS-045) consultado
pelo modulo `clientes` antes de anonimizar. Se cliente tem OS aberta,
solicitacao LGPD art. 18 V eh ENFILEIRADA (nao executada) e fica
esperando.

Trigger desta saga: evento `OS.Concluida` (ou `OS.Cancelada` /
`OS.Faturada` / `OS.Paga` — qualquer transicao terminal). Quando o
ultimo OS aberto do cliente fecha, saga re-tenta a anonimizacao
publicando `Cliente.AnonimizacaoSolicitadaRetry`.

PADRAO Spike: saga ESCRITA aqui contem APENAS o consumer que observa
transicao terminal de OS; modulo `clientes` ouve
`Cliente.AnonimizacaoSolicitadaRetry` e executa anonimizacao (Marco 1
ja tem use case `anonimizar_cliente`).

Estado da saga: rastreado por `EventoDeOS.tipo='os_concluida'` +
predicate `cliente_tem_os_aberta` (consulta direta).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID = "os.saga.anonimizacao_re_tentar"

# Estados terminais que LIBERAM retentativa de anonimizacao.
ESTADOS_TERMINAIS = frozenset({"concluida", "cancelada", "faturada", "paga"})


@consumer_idempotente(consumer_id=CONSUMER_ID)
def handle_os_em_estado_terminal(envelope: dict[str, Any]) -> None:
    """STUB Marco 3 (GATE-OS-ANON-RETRY-1): consulta predicate + LOGA decisao.

    Comportamento atual: quando OS entra em estado terminal, verifica
    se cliente liberou TODAS as OS abertas (predicate
    `cliente_tem_os_aberta`). Se zero pendentes, apenas LOGA — a
    publicacao de `Cliente.AnonimizacaoSolicitadaRetry` depende de
    Marco 1 ter `tabela_anonimizacao_pendente` (GATE Wave A).

    Docstring reflete o corpo: predicate + log. Saga completa fica
    em Wave A junto com retentativa real da anonimizacao.
    """
    payload = envelope.get("payload", {})
    os_id_raw = payload.get("os_id")
    if os_id_raw is None:
        return  # evento nao traz os_id — ignora
    try:
        os_uuid = UUID(str(os_id_raw))
    except (ValueError, TypeError):
        return

    from src.infrastructure.ordens_servico.models import OS

    os_obj = OS.objects.filter(id=os_uuid).only("cliente_id", "estado", "tenant_id").first()
    if os_obj is None or os_obj.cliente_id is None:
        return  # cliente ja anonimizado OR OS inexistente
    if os_obj.estado not in ESTADOS_TERMINAIS:
        return  # evento nao terminal — ignora

    # Resta alguma OS NAO-terminal pra este cliente?
    pendentes = OS.objects.filter(
        cliente_id=os_obj.cliente_id,
    ).exclude(estado__in=ESTADOS_TERMINAIS).exclude(id=os_uuid).count()
    if pendentes > 0:
        logger.debug(
            "os.saga.anonimizacao_re_tentar: cliente=%s ainda tem %d OS pendentes — aguarda",
            os_obj.cliente_id,
            pendentes,
        )
        return

    # TODO Marco 1 (clientes) — publicar evento Cliente.AnonimizacaoSolicitadaRetry
    # via event_helpers. Consumer Marco 1 escuta e executa
    # `anonimizar_cliente(cliente_id)` (use case existente).
    # Aqui apenas LOGA — implementacao real do publish entra junto com
    # `tabela_anonimizacao_pendente` (Marco 1 nao tem ainda; adiar
    # com GATE-OS-ANON-RETRY-1).
    logger.info(
        "os.saga.anonimizacao_re_tentar: cliente=%s liberado (zero OS pendente) — "
        "TODO publicar Cliente.AnonimizacaoSolicitadaRetry (GATE-OS-ANON-RETRY-1)",
        os_obj.cliente_id,
    )
