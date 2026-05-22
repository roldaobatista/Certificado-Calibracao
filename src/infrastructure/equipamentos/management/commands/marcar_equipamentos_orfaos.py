"""T-EQP-054 (US-EQP-006 AC-EQP-006-7 / P-EQP-T9) — sweep cross-tenant
detectando equipamentos com `cliente_atual_id IS NULL` que NAO estao
em status terminal e marcando-os como `orfao_pendente_decisao`.

Defesa em profundidade do trigger PG
`equipamento_anti_orfao_imediato_trg` (migration 0002).

Uso:
    python manage.py marcar_equipamentos_orfaos [--tenant <uuid>]

Wave A: agendamento via Procrastinate (1x/dia 03:00 BRT).
"""

from __future__ import annotations

from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from src.infrastructure.equipamentos.services_orfaos import (
    marcar_equipamentos_orfaos_pendentes,
)
from src.infrastructure.multitenant.jobs import (
    iter_tenants_ativos,
    processar_em_contexto_tenant,
)
from src.infrastructure.tenant.models import Tenant


class Command(BaseCommand):
    help = (
        "Marca equipamentos com cliente_atual_id NULL fora de status "
        "terminal como orfao_pendente_decisao + publica "
        "equipamento.orfao_marcado_pelo_job."
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
            tenants = list(iter_tenants_ativos())

        resultados = processar_em_contexto_tenant(
            lambda tenant: marcar_equipamentos_orfaos_pendentes(
                tenant_id=tenant.id
            ),
            tenants=tenants,
        )
        total = 0
        for tenant_id, marcados in resultados.items():
            n = len(marcados)
            total += n
            if n:
                self.stdout.write(f"[{tenant_id}] {n} orfao(s) marcado(s).")
        self.stdout.write(
            self.style.SUCCESS(
                f"Processados {len(tenants)} tenant(s); {total} orfao(s) "
                "marcado(s)."
            )
        )
