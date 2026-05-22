"""Management command T-EQP-019 (AC-EQP-002b-2 / P-EQP-R5).

Job que itera todos os tenants e expira `AprovacaoPendenteEquipamentoVersao`
com `sla_vencimento <= now()` em status `pendente`. Cada expiracao
publica `equipamento.versao_expirada` (cadeia + bus_outbox) +
opcionalmente alerta P2 (a cravar em T-EQP-019b — observabilidade).

Schedule recomendado (Procrastinate Wave A): diario 03:00 BRT.
Em Marco 2 roda manualmente ou via cron externo:
    python manage.py processar_aprovacoes_expiradas_equipamento

Output: linha por tenant com contagem de aprovacoes expiradas. Exit 0
mesmo se contagem == 0 (idempotente).
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from src.infrastructure.equipamentos.services_aprovacao import (
    expirar_aprovacoes_vencidas,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.tenant.models import Tenant


class Command(BaseCommand):
    help = (
        "Expira AprovacaoPendenteEquipamentoVersao com SLA vencido. "
        "Itera todos os tenants ativos. Idempotente."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        total_expiradas = 0
        for tenant in Tenant.objects.all():
            with run_in_tenant_context(tenant.id):
                resultados = expirar_aprovacoes_vencidas(tenant_id=tenant.id)
            if resultados:
                self.stdout.write(
                    f"tenant={tenant.slug} expirou {len(resultados)} aprovacoes"
                )
                total_expiradas += len(resultados)
        self.stdout.write(self.style.SUCCESS(
            f"OK — total expiradas: {total_expiradas}"
        ))
