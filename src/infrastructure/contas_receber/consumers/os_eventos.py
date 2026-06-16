"""Consumers de eventos de OS → contas_receber (Fatia 3a — T-CR-041 / D-CR-12).

Dois consumers idempotentes (ADR-0033), registrados em `apps.py:ready()`:

  - `handle_os_concluida`  ← `os.concluida` (enriquecido no outbox por T-CR-040):
      cria `Titulo` (origem=OS) e publica `contas_receber.titulo_emitido` + `os.faturada`.
  - `handle_os_reaberta`   ← `os.reaberta`:
      cancela o título da OS se SEM pagamento; mantém se houver pagamento (AC-CR-006-2).

Garantias (todas dentro da `transaction.atomic` aberta pelo `@consumer_idempotente`):
  - Idempotência de replay: `consumer_idempotencia(consumer_id, event_id)` (decorator).
  - Idempotência de negócio: `existe_titulo_ativo_para_os` (soft) + `UNIQUE(tenant_id,
    os_id_origem) WHERE estado != cancelado` (hard) + advisory lock (corrida de workers).
  - `perfil_no_evento` do ENVELOPE (D-CR-6) — nunca relido no worker; `None` → fail-closed.
  - Tenant suspenso → `TenantSuspensoEmissaoBloqueada` → rollback (decorator desfaz a marca
    de idempotência) → mensagem reprocessa ao reativar (R11 / ADR-0035 / PRD §10).

NÃO importa DRF nem SDK de gateway. `os.faturada` é namespace do agregado dono do
estado (OS) — publicado por CR ao faturar (TL-CR-02 / D-CR-12).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from django.db import connection

from src.application.contas_receber import (
    cancelar_titulo,
    criar_titulo_a_partir_de_os,
)
from src.domain.contas_receber.erros import (
    PerfilIndeterminado,
    TenantSuspensoEmissaoBloqueada,
    TituloComPagamentoParcial,
)
from src.infrastructure.bus.consumer_base import consumer_idempotente
from src.infrastructure.contas_receber.repositories import DjangoTituloRepository

logger = logging.getLogger(__name__)

CONSUMER_ID_OS_CONCLUIDA = "contas_receber.consumer.os_concluida"
CONSUMER_ID_OS_REABERTA = "contas_receber.consumer.os_reaberta"


def _advisory_lock(chave: str) -> None:
    """Advisory lock transacional (vive até o COMMIT do `atomic` do decorator)."""
    with connection.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [chave])


def _verificar_tenant_ativo(tenant_id: UUID) -> None:
    """R11 / ADR-0035: consumer NÃO cria título se tenant suspenso/cancelado.

    Levanta `TenantSuspensoEmissaoBloqueada` — o rollback do `@consumer_idempotente`
    desfaz a marca de idempotência, então a mensagem reprocessa quando o tenant
    reativar (PRD §10). `tenants` é tabela de plano-de-controle (sem RLS) — legível.
    """
    from src.infrastructure.tenant.models import StatusLifecycle, Tenant

    tenant = Tenant.objects.filter(id=tenant_id).only("status_lifecycle").first()
    if tenant is None:
        raise TenantSuspensoEmissaoBloqueada(
            f"tenant {tenant_id} inexistente — auto-faturamento bloqueado (fail-closed)."
        )
    if tenant.status_lifecycle in (
        StatusLifecycle.SUSPENSO,
        StatusLifecycle.CANCELADO,
    ):
        raise TenantSuspensoEmissaoBloqueada(
            f"tenant {tenant_id} em estado '{tenant.status_lifecycle}' — auto-faturamento "
            "bloqueado (PRD §10 / ADR-0035 / R-CR-NOVO-3); reprocessa ao reativar."
        )


def _publicar(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    resource_summary: str,
) -> None:
    """Publica evento (cadeia hash + outbox) na tx do decorator. Import local."""
    from src.infrastructure.audit.event_helpers import publicar_evento

    publicar_evento(
        acao=acao,
        payload=payload,
        causation_id=causation_id,
        tenant_id=tenant_id,
        resource_summary=resource_summary,
    )


def _os_id_e_tenant(envelope: dict[str, Any], consumer: str) -> tuple[UUID, UUID] | None:
    """Extrai e valida `os_id` (payload) + `tenant_id` (envelope). None → no-op."""
    payload = envelope.get("payload", {})
    os_id_raw = payload.get("os_id")
    tenant_raw = envelope.get("tenant_id")
    if not os_id_raw or not tenant_raw:
        logger.warning("%s: envelope sem os_id/tenant_id — no-op", consumer)
        return None
    try:
        return UUID(str(os_id_raw)), UUID(str(tenant_raw))
    except (ValueError, TypeError):
        logger.warning("%s: os_id/tenant_id inválido — no-op", consumer)
        return None


@consumer_idempotente(consumer_id=CONSUMER_ID_OS_CONCLUIDA)
def handle_os_concluida(envelope: dict[str, Any]) -> None:
    """`os.concluida` enriquecida → cria Titulo (origem=OS) + publica eventos (D-CR-12)."""
    ids = _os_id_e_tenant(envelope, "handle_os_concluida")
    if ids is None:
        return
    os_id, tenant_id = ids

    payload = envelope.get("payload", {})
    cliente_hash = payload.get("cliente_referencia_hash")
    valor_raw = payload.get("valor_total_centavos")
    # os.concluida não-enriquecida (legado / publicada antes de T-CR-040) → no-op.
    if not cliente_hash or valor_raw is None:
        logger.info(
            "handle_os_concluida: os.concluida sem enriquecimento de faturamento "
            "(os_id=%s) — no-op",
            os_id,
        )
        return
    try:
        valor_centavos = int(valor_raw)
    except (ValueError, TypeError):
        logger.warning("handle_os_concluida: valor_total_centavos inválido — no-op")
        return
    # OS sem valor faturável (todas atividades canceladas — INV-OS-FAT-001) → no-op.
    if valor_centavos <= 0:
        logger.info(
            "handle_os_concluida: OS %s sem valor faturável (centavos=%s) — sem título",
            os_id,
            valor_centavos,
        )
        return

    # R11 / ADR-0035: tenant suspenso → dead-letter (reprocessa ao reativar).
    _verificar_tenant_ativo(tenant_id)

    # D-CR-6 fail-closed: perfil vem do ENVELOPE, nunca relido no worker.
    perfil = envelope.get("perfil_no_evento")
    if not perfil:
        raise PerfilIndeterminado(
            f"handle_os_concluida: os.concluida (os_id={os_id}) sem perfil_no_evento "
            "no envelope — fail-closed (D-CR-6, dead-letter)."
        )

    cliente_atual_raw = payload.get("cliente_atual_id")
    cliente_atual_id = UUID(str(cliente_atual_raw)) if cliente_atual_raw else None
    event_id = UUID(str(envelope["event_id"]))

    repo = DjangoTituloRepository()
    # Serializa corrida entre workers (soft check + UNIQUE são as outras camadas).
    _advisory_lock(f"cr:os_concluida:{tenant_id}:{os_id}")
    inp = criar_titulo_a_partir_de_os.CriarTituloAPartirDeOSInput(
        tenant_id=tenant_id,
        os_id=os_id,
        cliente_referencia_hash=str(cliente_hash),
        cliente_key_id=str(payload.get("cliente_key_id") or ""),
        valor_centavos=valor_centavos,
        perfil_no_evento=str(perfil),
        cliente_atual_id=cliente_atual_id,
    )
    out = criar_titulo_a_partir_de_os.executar(inp, repo=repo)
    if out.ja_existia or out.titulo is None:
        logger.info(
            "handle_os_concluida: título de OS %s já existe — idempotente", os_id
        )
        return

    titulo = out.titulo
    _publicar(
        acao="contas_receber.titulo_emitido",
        payload={
            "titulo_id": str(titulo.titulo_id),
            "cliente_referencia_hash": titulo.cliente_referencia.hash_original,
            "valor_centavos": titulo.valor_original.centavos,
            "data_vencimento": titulo.data_vencimento.isoformat(),
            "categoria_receita": titulo.categoria_receita.value,
            "perfil_no_evento": titulo.perfil_no_evento,
            "meio": titulo.meio.value,
            "origem": titulo.origem.value,
            "os_id_origem": str(os_id),
        },
        causation_id=event_id,
        tenant_id=tenant_id,
        resource_summary=f"titulo_receber {titulo.titulo_id} emitido (os {os_id})",
    )
    _publicar(
        acao="os.faturada",
        payload={"os_id": str(os_id)},
        causation_id=event_id,
        tenant_id=tenant_id,
        resource_summary=f"os {os_id} faturada (titulo {titulo.titulo_id})",
    )
    logger.info(
        "handle_os_concluida: título %s criado para OS %s (auto-fatura)",
        titulo.titulo_id,
        os_id,
    )


@consumer_idempotente(consumer_id=CONSUMER_ID_OS_REABERTA)
def handle_os_reaberta(envelope: dict[str, Any]) -> None:
    """`os.reaberta` → cancela título da OS se SEM pagamento; mantém se houver (AC-CR-006-2)."""
    ids = _os_id_e_tenant(envelope, "handle_os_reaberta")
    if ids is None:
        return
    os_id, tenant_id = ids

    repo = DjangoTituloRepository()
    _advisory_lock(f"cr:os_reaberta:{tenant_id}:{os_id}")
    titulo = repo.obter_titulo_ativo_por_os(tenant_id=tenant_id, os_id=os_id)
    if titulo is None:
        logger.info(
            "handle_os_reaberta: OS %s sem título ativo — nada a cancelar", os_id
        )
        return

    event_id = UUID(str(envelope["event_id"]))
    try:
        out = cancelar_titulo.executar(
            cancelar_titulo.CancelarTituloInput(
                tenant_id=tenant_id,
                titulo_id=titulo.titulo_id,
                razao="os_reaberta",
            ),
            repo=repo,
        )
    except TituloComPagamentoParcial:
        # AC-CR-006-2: título com pagamento (parcial/total) NÃO é cancelado na reabertura.
        logger.info(
            "handle_os_reaberta: título %s da OS %s tem pagamento — mantido (AC-CR-006-2)",
            titulo.titulo_id,
            os_id,
        )
        return

    _publicar(
        acao="contas_receber.titulo_cancelado",
        payload={
            "titulo_id": str(titulo.titulo_id),
            "razao": "os_reaberta",
            "cancelado_em": out.cancelado_em.isoformat(),
            "perfil_no_evento": titulo.perfil_no_evento,
            "os_id_origem": str(os_id),
        },
        causation_id=event_id,
        tenant_id=tenant_id,
        resource_summary=f"titulo_receber {titulo.titulo_id} cancelado (os {os_id} reaberta)",
    )
    logger.info(
        "handle_os_reaberta: título %s da OS %s cancelado (reabertura)",
        titulo.titulo_id,
        os_id,
    )
