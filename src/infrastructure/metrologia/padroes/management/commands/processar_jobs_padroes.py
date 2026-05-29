"""T-PAD-050 — Management command do job P6 M5 padroes.

Uso:
    python manage.py processar_jobs_padroes [--tenant <uuid>]

Diferente do M4 calibracao (que rodava em modo STUB-WAVE-A com listas
vazias porque os adapters Django nao existiam), o M5 padroes JA TEM
adapters reais (P5). Este command carrega snapshots do Django ORM, chama
a funcao pura `alertar_padroes_pendencias.executar`, e loga/emite os
alertas estruturados.

Os 4 tipos de pendencia varridos (T-PAD-050):
  RECAL_VENCENDO              — proximo_recal <= hoje + 30d (ou vencido).
  VI_PENDENTE                 — ultima VI + intervalo_vi_meses <= hoje+30d.
  RECAL_RETORNO_ATRASADO      — recal ENVIADO ha > 90 dias.
  RECAL_APROVACAO_RT_PENDENTE — recal RETORNADO ha > Nd sem aprovacao RT.

Cada tenant roda em `run_in_tenant_context` (RLS ativa + ContextVars —
SEG / INV-TENANT-001). Todo log carrega `tenant_id` + `correlation_id`
(OBS-002).

NOTA GATE-OBS-PAD-WORM-1 (diferido p/ fatia de integracao de eventos):
por ora os alertas sao LOGADOS estruturados; a publicacao na cadeia WORM
global `padrao.*` via `publicar_evento` entra junto com as mutacoes REST
no D-PAD-6 (antes do P9). Frequencia recomendada Wave A: diaria 04:00 BRT.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max

if TYPE_CHECKING:
    # Bloco TYPE_CHECKING nao roda em runtime — nao reintroduz o problema de
    # ordenacao do app registry que motiva os imports locais em _carregar_e_alertar.
    from src.application.metrologia.padroes.jobs.alertar_padroes_pendencias import (
        AlertaPadrao,
    )

logger = logging.getLogger(__name__)


def _log_extra(tenant_id: UUID, correlation_id: UUID, **kw: Any) -> dict[str, Any]:
    """Dict canonico de campos estruturados (OBS-002): tenant_id + correlation_id."""
    base: dict[str, Any] = {
        "tenant_id": str(tenant_id),
        "correlation_id": str(correlation_id),
    }
    base.update(kw)
    return base


def _carregar_e_alertar(tenant_id: UUID, agora: datetime) -> list[AlertaPadrao]:
    """Carrega snapshots do ORM (RLS ativa) e chama a funcao pura.

    Importacoes locais: command so e descoberto via autodiscovery do Django,
    entao adia import de models/dominio pra apos o setup do app registry.
    """
    from src.application.metrologia.padroes.jobs.alertar_padroes_pendencias import (
        PadraoComUltimaVI,
        executar,
    )
    from src.domain.metrologia.padroes.enums import EstadoPadrao, StatusRecal
    from src.infrastructure.metrologia.padroes import mappers
    from src.infrastructure.metrologia.padroes.models import (
        PadraoMetrologico,
        RecalExternoPadrao,
        VerificacaoIntermediaria,
    )
    from src.infrastructure.metrologia.padroes.repositories import (
        DjangoRecalExternoRepository,
    )

    # Padroes EM_USO vivos (defesa em profundidade: filtro tenant explicito
    # alem da RLS). proximo_recal / VI dependem desses.
    padroes_qs = list(
        PadraoMetrologico.objects.filter(
            tenant_id=tenant_id,
            estado=EstadoPadrao.EM_USO.value,
            revogado_em__isnull=True,
        )
    )
    padroes_em_uso = [mappers.model_para_snapshot(p) for p in padroes_qs]

    # Ultima VI por padrao (1 query agregada — evita N+1).
    ultima_vi_por_padrao: dict[UUID, datetime] = {
        row["padrao_id"]: row["ultima"]
        for row in VerificacaoIntermediaria.objects.filter(
            tenant_id=tenant_id,
            padrao_id__in=[p.id for p in padroes_em_uso],
        )
        .values("padrao_id")
        .annotate(ultima=Max("data_vi"))
    }
    padroes_vi = [
        PadraoComUltimaVI(
            padrao=snap, ultima_vi_em=ultima_vi_por_padrao.get(snap.id)
        )
        for snap in padroes_em_uso
    ]

    recals_enviados = [
        DjangoRecalExternoRepository._to_snapshot(r)
        for r in RecalExternoPadrao.objects.filter(
            tenant_id=tenant_id, status=StatusRecal.ENVIADO.value
        )
    ]
    recals_retornados = [
        DjangoRecalExternoRepository._to_snapshot(r)
        for r in RecalExternoPadrao.objects.filter(
            tenant_id=tenant_id,
            status=StatusRecal.RETORNADO.value,
            aprovado_rt_em__isnull=True,
        )
    ]

    return executar(
        padroes_em_uso=padroes_em_uso,
        padroes_vi=padroes_vi,
        recals_enviados=recals_enviados,
        recals_retornados=recals_retornados,
        agora=agora,
    )


class Command(BaseCommand):
    help = "Roda o job P6 M5 padroes (T-PAD-050) — alertas de pendencia por tenant."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--tenant",
            type=str,
            help="Processa apenas o tenant_id especificado (UUID).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        from src.infrastructure.multitenant.connection import run_in_tenant_context
        from src.infrastructure.tenant.models import Tenant

        tenant_filter = options.get("tenant")
        if tenant_filter:
            try:
                tenant_uuid = UUID(tenant_filter)
            except (ValueError, TypeError) as exc:
                raise CommandError(f"--tenant invalido: {exc}") from exc
            tenants = Tenant.objects.filter(id=tenant_uuid)
            if not tenants.exists():
                raise CommandError(f"Tenant {tenant_uuid} nao encontrado.")
        else:
            tenants = Tenant.objects.all()

        agora = datetime.now(UTC)
        # Correlation ID unico por execucao (agrega trail por varredura).
        correlation_id = uuid4()

        for tenant in tenants:
            try:
                with run_in_tenant_context(tenant.id):
                    alertas = _carregar_e_alertar(tenant.id, agora)
                # Log estruturado por alerta (OBS-002 — tenant + correlation).
                for a in alertas:
                    logger.warning(
                        "processar_jobs_padroes alerta tipo=%s padrao=%s "
                        "serie=%s severidade=%s dias=%d",
                        a.tipo.value,
                        a.padrao_id,
                        a.numero_serie,
                        a.severidade,
                        a.dias,
                        extra=_log_extra(
                            tenant.id,
                            correlation_id,
                            tipo=a.tipo.value,
                            padrao_id=str(a.padrao_id),
                            severidade=a.severidade,
                            referencia_id=(
                                str(a.referencia_id) if a.referencia_id else None
                            ),
                        ),
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  OK  tenant={tenant.id} -> {len(alertas)} alerta(s)"
                    )
                )
            except Exception as exc:  # — wrapper top-level por tenant
                self.stdout.write(
                    self.style.ERROR(f"  ERR tenant={tenant.id} -> {exc}")
                )
                logger.exception(
                    "processar_jobs_padroes falhou no tenant",
                    extra=_log_extra(tenant.id, correlation_id),
                )
