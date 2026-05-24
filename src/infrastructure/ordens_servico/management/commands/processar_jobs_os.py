"""Roda os 4 jobs periodicos M3 OS (T-OS-090..093) para todos os tenants.

Uso:
    python manage.py processar_jobs_os [--tenant <uuid>] [--job <nome>]

Sem --job: roda todos. Job: `watchdog_calibracao_link` | `truncar_geo_lgpd`
| `retry_anonimizacao_pendente` | `detectar_sla_breach`.

Wave A: agendamento periodico via procrastinate (1x dia 03:00 UTC).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.jobs import (
    detectar_sla_breach,
    retry_anonimizacao_pendente,
    truncar_geo_lgpd,
    watchdog_calibracao_link,
)
from src.infrastructure.tenant.models import Tenant

JOBS: dict[str, Callable[..., Any]] = {
    "watchdog_calibracao_link": watchdog_calibracao_link,
    "truncar_geo_lgpd": truncar_geo_lgpd,
    "retry_anonimizacao_pendente": retry_anonimizacao_pendente,
    "detectar_sla_breach": detectar_sla_breach,
}


class Command(BaseCommand):
    help = "Roda jobs periodicos M3 OS (T-OS-090..093) para todos os tenants."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            type=str,
            help="Processa apenas o tenant_id especificado (UUID).",
        )
        parser.add_argument(
            "--job",
            type=str,
            choices=list(JOBS.keys()),
            help="Executa apenas o job nomeado (default: todos).",
        )

    def handle(self, *args, **options):
        tenant_filtro = options.get("tenant")
        if tenant_filtro:
            try:
                tenants = [Tenant.objects.get(id=UUID(tenant_filtro))]
            except (Tenant.DoesNotExist, ValueError) as exc:
                raise CommandError(f"tenant invalido: {exc}") from exc
        else:
            tenants = list(Tenant.objects.all())

        job_filtro = options.get("job")
        jobs_a_rodar = {job_filtro: JOBS[job_filtro]} if job_filtro else JOBS

        for tenant in tenants:
            with run_in_tenant_context(tenant.id):
                for nome, fn in jobs_a_rodar.items():
                    try:
                        resultado = fn(tenant_id=tenant.id)
                    except Exception as exc:
                        self.stderr.write(
                            self.style.ERROR(
                                f"[{tenant.slug}] {nome}: erro {exc!r}"
                            )
                        )
                        continue
                    self.stdout.write(
                        f"[{tenant.slug}] {nome}: {resultado!r}"
                    )
        self.stdout.write(self.style.SUCCESS(f"Concluido — {len(tenants)} tenants."))
