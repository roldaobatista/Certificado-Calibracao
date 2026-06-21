"""Consumers de eventos cross-módulo do caixa_tecnico (Fatia 3b — T-CT-050).

Eventos consumidos:
  colaborador.desligado → marca o ``CaixaTecnico`` do técnico como desligado
    (``desligado_em``) → novos lançamentos passam a levantar ``CaixaTecnicoDesligado``
    (409) na camada de aplicação.

Regras (D-CT-11 / T-CT-050 / R7):
  - ``@consumer_idempotente`` (ADR-0033 / INV-BUS-001): replay não re-executa.
  - **Perfil lido do ENVELOPE**, nunca de ``obter_perfil_tenant_corrente()`` — o worker
    roda sem request context.
  - **Fail-closed**: técnico desligado NÃO deve ter caixa ativo; o estado seguro é
    ``desligado``. Por isso o handler PROCEDE com o desligamento mesmo se ``perfil_no_evento``
    faltar (ao contrário do consumer da agenda, cuja ação — cancelar eventos — é
    perfil-sensível e por isso no-opa). Não marcar deixaria um técnico desligado com caixa
    ATIVO, o estado inseguro.
  - Naturalmente idempotente: se o caixa já está desligado, não re-grava.

Molde: ``src/infrastructure/agenda/consumers/colaborador_eventos.py``.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any
from uuid import UUID

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

_LOG = "caixa_tecnico.consumer.colaborador_desligado"


@consumer_idempotente(consumer_id="caixa_tecnico.consumer.colaborador_desligado")
def handle_colaborador_desligado(envelope: dict[str, Any]) -> None:
    """colaborador.desligado → desliga o ``CaixaTecnico`` do técnico (fail-closed).

    O worker invoca este handler DENTRO de ``run_in_tenant_context`` (RLS ativo) — o
    handler não abre contexto de tenant. A marca de idempotência + o side-effect entram
    na mesma transação (decorator).
    """
    raw_tenant = envelope.get("tenant_id")
    if not raw_tenant:
        logger.warning("%s: tenant_id ausente — no-op", _LOG)
        return
    try:
        tenant_id = UUID(str(raw_tenant))
    except (ValueError, TypeError):
        logger.warning("%s: tenant_id inválido: %r — no-op", _LOG, raw_tenant)
        return

    # Perfil lido do ENVELOPE (T-CT-050 / R7) — NUNCA obter_perfil_tenant_corrente().
    # Usado só para trilha; o desligamento é a ação fail-closed (segura) e procede mesmo
    # sem perfil (ver docstring do módulo).
    perfil = envelope.get("perfil_no_evento")

    payload = envelope.get("payload", {})
    colaborador_id_raw = payload.get("colaborador_id")
    if not colaborador_id_raw:
        logger.warning("%s: colaborador_id ausente no payload — no-op", _LOG)
        return
    try:
        colaborador_id = UUID(str(colaborador_id_raw))
    except (ValueError, TypeError):
        logger.warning("%s: colaborador_id inválido: %r — no-op", _LOG, colaborador_id_raw)
        return

    from django.utils import timezone

    from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
    from src.infrastructure.caixa_tecnico.repositories import CaixaTecnicoRepository

    # Resolve colaborador_id → tecnico_referencia_hash (só o hexdigest — mesmo padrão de
    # gravação do caixa). Sem PII crua no consumer.
    tecnico_hash = hashear_pii_com_salt_tenant(str(colaborador_id), tenant_id).split(":", 1)[1]

    repo = CaixaTecnicoRepository()
    caixa = repo.obter_por_hash(tenant_id, tecnico_hash)
    if caixa is None:
        logger.info(
            "%s: sem caixa para colaborador=%s tenant=%s (perfil=%s) — no-op",
            _LOG,
            colaborador_id,
            tenant_id,
            perfil,
        )
        return
    if caixa.esta_desligado:
        logger.info(
            "%s: caixa já desligado para colaborador=%s — no-op idempotente", _LOG, colaborador_id
        )
        return

    caixa_desligado = dataclasses.replace(caixa, desligado_em=timezone.now())
    repo.atualizar(tenant_id, caixa_desligado)
    logger.info(
        "%s: caixa desligado colaborador=%s tenant=%s (perfil=%s)",
        _LOG,
        colaborador_id,
        tenant_id,
        perfil,
    )
