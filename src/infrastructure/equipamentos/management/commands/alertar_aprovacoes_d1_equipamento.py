"""T-EQP-054 (US-EQP-002b AC-EQP-002b-2 / P-EQP-R5) — alerta D-1
antes do SLA da aprovacao vencer.

Localiza `AprovacaoPendenteEquipamentoVersao` em status PENDENTE com
`sla_vencimento` ate D+1 (24h) e publica
`equipamento.versao_aprovacao_alerta_d1` (consumer real Wave A envia
email/push ao decisor).

Uso:
    python manage.py alertar_aprovacoes_d1_equipamento [--tenant <uuid>] \\
        [--horas-max <int>]

Wave A: agendamento via Procrastinate 1x/dia 10:00 BRT (mais cedo que
expirar para dar ao decisor a janela do dia util).
"""

from __future__ import annotations

from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from src.infrastructure.equipamentos.services_aprovacao import (
    alertar_aprovacoes_d1,
)
from src.infrastructure.multitenant.jobs import (
    iter_tenants_ativos,
    processar_em_contexto_tenant,
)
from src.infrastructure.tenant.models import Tenant


class Command(BaseCommand):
    help = (
        "Publica equipamento.versao_aprovacao_alerta_d1 para aprovacoes "
        "PENDENTES vencendo em ate `horas_maximas` (default 24h)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            type=str,
            help="Processa apenas o tenant_id especificado (UUID).",
        )
        parser.add_argument(
            "--horas-max",
            type=int,
            default=24,
            help="Janela maxima em horas para incluir aprovacao no alerta.",
        )

    def handle(self, *args, **options):
        tenant_id_filtro = options.get("tenant")
        horas_max = options["horas_max"]
        if tenant_id_filtro:
            try:
                tenants = [Tenant.objects.get(id=UUID(tenant_id_filtro))]
            except (Tenant.DoesNotExist, ValueError) as exc:
                raise CommandError(f"tenant invalido: {exc}") from exc
        else:
            tenants = list(iter_tenants_ativos())

        resultados = processar_em_contexto_tenant(
            lambda tenant: alertar_aprovacoes_d1(
                tenant_id=tenant.id,
                horas_maximas_para_alerta=horas_max,
            ),
            tenants=tenants,
        )
        total = 0
        for tenant_id, alertadas in resultados.items():
            n = len(alertadas)
            total += n
            if n:
                self.stdout.write(
                    f"[{tenant_id}] {n} aprovacao(oes) alertada(s)."
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Processados {len(tenants)} tenant(s); {total} alerta(s) "
                "publicado(s)."
            )
        )
