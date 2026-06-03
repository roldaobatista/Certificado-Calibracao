"""T-LIC-051 (US-LIC-002) — agenda alertas de vencimento de documentos regulatórios.

Para cada tenant, lê os documentos NÃO-revogados na maior janela de alerta
(`agora + 90d`), chama a função pura `verificar_alertas_licencas` (D-90/60/30/15/7) e
agenda via `AlertaRepository.agendar` — idempotente pela UNIQUE
`(tenant, documento, janela_dias)` (reexecução diária não duplica).

Uso:
    python manage.py verificar_alertas_licencas [--tenant <uuid>]

Wave A: agendamento via Procrastinate 1x/dia. Envio real de e-mail é diferido
(ADR-0060 — canal default DASHBOARD); aqui só materializa o alerta PENDENTE.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from src.application.metrologia.licencas_acreditacoes.jobs.verificar_alertas_licencas import (
    verificar_alertas_licencas,
)
from src.infrastructure.metrologia.licencas_acreditacoes.query_service import (
    listar_documentos_para_alerta,
)
from src.infrastructure.metrologia.licencas_acreditacoes.repositories import (
    DjangoAlertaRepository,
)
from src.infrastructure.multitenant.jobs import (
    iter_tenants_ativos,
    processar_em_contexto_tenant,
)
from src.infrastructure.tenant.models import Tenant


class Command(BaseCommand):
    help = (
        "Agenda AlertaVencimento PENDENTE para documentos regulatórios entrando nas "
        "janelas D-90/60/30/15/7 (idempotente)."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--tenant",
            type=str,
            help="Processa apenas o tenant_id especificado (UUID).",
        )

    def _agendar_para_tenant(self, tenant: Tenant) -> int:
        agora = timezone.now().date()
        snapshots = listar_documentos_para_alerta(tenant_id=tenant.id, agora=agora)
        alertas = verificar_alertas_licencas(snapshots, agora=agora)
        repo = DjangoAlertaRepository()
        for alerta in alertas:
            repo.agendar(alerta)
        return len(alertas)

    def handle(self, *args: Any, **options: Any) -> None:
        tenant_id_filtro = options.get("tenant")
        if tenant_id_filtro:
            try:
                tenants = [Tenant.objects.get(id=UUID(tenant_id_filtro))]
            except (Tenant.DoesNotExist, ValueError) as exc:
                raise CommandError(f"tenant invalido: {exc}") from exc
        else:
            tenants = list(iter_tenants_ativos())

        resultados = processar_em_contexto_tenant(
            self._agendar_para_tenant, tenants=tenants
        )
        total = sum(resultados.values())
        for tenant_id, n in resultados.items():
            if n:
                self.stdout.write(f"[{tenant_id}] {n} alerta(s) agendado(s).")
        self.stdout.write(
            self.style.SUCCESS(
                f"Processados {len(tenants)} tenant(s); {total} alerta(s) agendado(s)."
            )
        )
