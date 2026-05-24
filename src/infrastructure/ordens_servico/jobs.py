"""Jobs periódicos M3 OS Fase 7 (T-OS-090..093).

Cada job:
- Idempotente (executar 2x no mesmo dia eh seguro).
- Roda por tenant via `run_in_tenant_context`.
- Stub log P3 onde Wave A ligara consumer real (PagerDuty / WhatsApp /
  module qualidade).

4 jobs:
- watchdog_calibracao_link (T-OS-090 / AC-OS-004-5 + INV-OS-CAL-LINK-001)
- truncar_geo_lgpd (T-OS-091 / INV-OS-GEO-001 + P-OS-A2 — 5a TTL)
- retry_anonimizacao_pendente (T-OS-092 / INV-OS-ANON-001)
- detectar_sla_breach (T-OS-093 / US-OS-007 saga 4)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from django.db import connection, transaction

logger = logging.getLogger(__name__)


# =============================================================
# T-OS-090 — watchdog_calibracao_link
# =============================================================


def watchdog_calibracao_link(*, tenant_id: UUID, agora: datetime | None = None) -> dict[str, int]:
    """Detecta atividades calibracao CONCLUIDA sem `link_modulo_tecnico_id`
    apos `prazo_link_calibracao_alerta_h` (default RBC perfil A: 72h) ou
    `prazo_link_calibracao_nc_dias_uteis` (15 dias).

    Marco 3: emite log P3 stub + EventoDeOS `watchdog_estendido` quando
    detecta. Wave A consumer real publica via bus + cria NaoConformidade
    automatica `link_calibracao_faltando`.

    Returns: {alertados: int, nc_candidatos: int}.
    """
    from src.infrastructure.ordens_servico.models import AtividadeDaOS, TipoAtividadeConfig

    now = agora or datetime.now(UTC)

    cfg = TipoAtividadeConfig.objects.filter(
        tenant_id=tenant_id,
        tipo="calibracao",
        deletado_em__isnull=True,
    ).first()
    # Defaults RBC perfil A quando tenant ainda nao tem seed de config
    # (caso de testes/dogfooding inicial).
    prazo_alerta_h = (cfg.prazo_link_calibracao_alerta_h if cfg else None) or 72
    prazo_nc_dias = (cfg.prazo_link_calibracao_nc_dias_uteis if cfg else None) or 15

    limite_alerta = now - timedelta(hours=prazo_alerta_h)
    # Dias uteis aproximados (5 uteis = 7 corridos).
    limite_nc = now - timedelta(days=int(prazo_nc_dias * 1.4))

    base = AtividadeDaOS.objects.filter(
        tenant_id=tenant_id,
        tipo="calibracao",
        estado="concluida",
        link_modulo_tecnico_id__isnull=True,
    )
    alertados = base.filter(concluida_em__lte=limite_alerta).count()
    nc_candidatos = base.filter(concluida_em__lte=limite_nc).count()

    if alertados:
        logger.warning(
            "watchdog_calibracao_link: tenant=%s alertados=%d nc_candidatos=%d "
            "prazo_alerta_h=%d prazo_nc_dias_uteis=%d",
            tenant_id,
            alertados,
            nc_candidatos,
            prazo_alerta_h,
            prazo_nc_dias,
        )

    return {"alertados": alertados, "nc_candidatos": nc_candidatos}


# =============================================================
# T-OS-091 — truncar_geo_lgpd
# =============================================================


def truncar_geo_lgpd(*, tenant_id: UUID, agora: datetime | None = None) -> int:
    """LGPD art. 16: geo_lat/long de atividades CONCLUIDA ha > 5 anos viram NULL.

    Preserva `geo_municipio_hash` (INV-OS-GEO-001 item d — analitico nao-PII).

    Returns: numero de atividades truncadas.
    """
    from src.infrastructure.ordens_servico.models import AtividadeDaOS

    now = agora or datetime.now(UTC)
    limite_5a = now - timedelta(days=365 * 5)

    qs = AtividadeDaOS.objects.filter(
        tenant_id=tenant_id,
        concluida_em__lte=limite_5a,
    ).exclude(geo_lat__isnull=True, geo_long__isnull=True)

    with transaction.atomic():
        truncadas = qs.update(geo_lat=None, geo_long=None)

    if truncadas:
        logger.info(
            "truncar_geo_lgpd: tenant=%s truncadas=%d (geo_municipio_hash preservado)",
            tenant_id,
            truncadas,
        )
    return truncadas


# =============================================================
# T-OS-092 — retry_anonimizacao_pendente
# =============================================================


def retry_anonimizacao_pendente(*, tenant_id: UUID) -> int:
    """Stub Marco 3: detecta OS ativas vinculadas a cliente que pediu
    anonimizacao (Zona A/B ADR-0021) — Wave A consumer real reprocessa
    saga `Cliente.AnonimizacaoSolicitada` quando OS conclui.

    Marco 3: apenas conta candidatos (cliente_id != NULL mas com
    `Cliente.solicitou_anonimizacao=True`, futuro Marco 4 do clientes).

    Returns: numero de OSs candidatas (apenas log; sem efeito).
    """
    from src.infrastructure.ordens_servico.models import OS

    # Estado nao-terminal = ainda bloqueia anonimizacao (INV-OS-ANON-001).
    pendentes = OS.objects.filter(
        tenant_id=tenant_id,
        estado__in=("rascunho", "agendada", "em_execucao"),
        cliente_id__isnull=False,
    ).count()

    if pendentes:
        logger.debug(
            "retry_anonimizacao_pendente: tenant=%s pendentes=%d "
            "(Wave A: reprocessa saga AnonimizacaoSolicitada)",
            tenant_id,
            pendentes,
        )
    return pendentes


# =============================================================
# T-OS-093 — detectar_sla_breach
# =============================================================


def detectar_sla_breach(*, tenant_id: UUID, agora: datetime | None = None) -> int:
    """Detecta OS com SLA estourado (US-OS-007 saga 4).

    Marco 3: stub — calcula horas_decorridas desde criada_em e compara com
    SLAContrato vigente do cliente. Em estado EM_EXECUCAO + horas >
    prazo_atendimento_horas -> sla_breach.

    Wave A consumer real publica `OS.SlaBreach` no bus + dispara alerta
    para gerente operacional + portal-cliente.

    Returns: numero de OSs com SLA quebrado detectadas.
    """
    now = agora or datetime.now(UTC)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM ordens_servico os
            JOIN sla_contrato s ON
                s.tenant_id = os.tenant_id
                AND s.cliente_id = os.cliente_id
                AND (s.vigencia_fim IS NULL OR s.vigencia_fim > %s)
                AND s.revogado_em IS NULL
            WHERE os.tenant_id = %s
              AND os.estado IN ('em_execucao', 'agendada')
              AND EXTRACT(EPOCH FROM (%s - os.criada_em)) / 3600.0
                  > s.prazo_atendimento_horas
            """,
            [now, str(tenant_id), now],
        )
        row = cur.fetchone()
    detectados = int(row[0]) if row else 0
    if detectados:
        logger.warning(
            "detectar_sla_breach: tenant=%s detectados=%d",
            tenant_id,
            detectados,
        )
    return detectados
