"""T-EQP-056 (US-EQP-006 AC-EQP-006-6 / P-EQP-R9) — itera tenants +
marca recebimentos provisorios com TTL D+7 vencido como
`expirado_descartado` + publica `sistema.provisorio_expirado` (alerta
P2 stub Marco 2; consumer real Wave A PagerDuty).

Uso:
    python manage.py processar_provisorios_expirados [--tenant <uuid>]

Wave A: agendamento via procrastinate D+1 (12:00 UTC).
"""

from __future__ import annotations

from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from src.infrastructure.equipamentos.services_provisorio import (
    marcar_provisorios_expirados,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.tenant.models import Tenant


class Command(BaseCommand):
    help = (
        "Marca recebimentos provisorios com TTL D+7 vencido como "
        "expirado_descartado e publica sistema.provisorio_expirado."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            type=str,
            help="Processa apenas o tenant_id especificado (UUID).",
        )

    def handle(self, *args, **options):
        tenant_id_filtro = options.get("tenant")
        if tenant_id_filtro:
            try:
                tenants = [Tenant.objects.get(id=UUID(tenant_id_filtro))]
            except (Tenant.DoesNotExist, ValueError) as exc:
                raise CommandError(f"tenant invalido: {exc}") from exc
        else:
            tenants = list(Tenant.objects.all())

        total = 0
        for tenant in tenants:
            with run_in_tenant_context(tenant.id):
                contagem = marcar_provisorios_expirados(tenant_id=tenant.id)
            if contagem:
                self.stdout.write(
                    f"[{tenant.slug}] {contagem} provisorios marcados como "
                    "expirado_descartado."
                )
            total += contagem
        self.stdout.write(
            self.style.SUCCESS(
                f"Processados {len(tenants)} tenant(s); {total} provisorios "
                "expirados."
            )
        )
