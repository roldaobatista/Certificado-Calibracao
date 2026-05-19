"""Popula o banco com dados sinteticos pra drill restore PG ser significativo.

Cria 5 tenants × 10k linhas de auditoria = 50k linhas (volume nao-trivial).
Roda em ~30s. Resultado: dump terá ~10-20 MiB, restore demora seg/min.

Uso:
    docker compose exec app poetry run python manage.py popular_drill
"""

from __future__ import annotations

from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db import transaction

from src.infrastructure.audit.services import registrar_auditoria
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)
from src.infrastructure.tenant.models import Tenant
from src.infrastructure.usuario.models import Usuario


class Command(BaseCommand):
    help = "Popula DB com 5 tenants x 10k auditorias pra drill restore PG ser significativo."

    def add_arguments(self, parser):
        parser.add_argument("--tenants", type=int, default=5)
        parser.add_argument("--linhas-por-tenant", type=int, default=10_000)

    def handle(self, *args, **options):
        n_tenants = options["tenants"]
        n_linhas = options["linhas_por_tenant"]

        self.stdout.write(
            self.style.NOTICE(f"Populando {n_tenants} tenants × {n_linhas} linhas...")
        )

        # Cria tenants + usuario por tenant
        tenants_e_usuarios = []
        with run_as_system():
            for _ in range(n_tenants):
                uid = uuid4().hex[:8]
                t = Tenant.objects.create(
                    slug=f"drill-pop-{uid}",
                    nome_fantasia=f"Drill Populator {uid}",
                )
                u = Usuario.objects.create_user(
                    email=f"drill-pop-{uid}@x.com",
                    password="drill-teste-12-chars",  # noqa: S106 -- credencial de drill local (comando dev-only), nunca usada em producao
                )
                tenants_e_usuarios.append((t, u))

        # Insere auditorias em batch (transacao por tenant pra nao saturar advisory lock)
        total = 0
        for t, u in tenants_e_usuarios:
            with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
                with transaction.atomic():
                    for i in range(n_linhas):
                        registrar_auditoria(
                            tenant_id=t.id,
                            usuario_id=u.id,
                            action=f"drill.evento.{i}",
                            resource_summary=f"recurso-{i}",
                            payload={"i": i, "tenant": str(t.id)},
                        )
                        total += 1
                        if total % 5000 == 0:
                            self.stdout.write(f"  ... {total} linhas inseridas")

        self.stdout.write(self.style.SUCCESS(f"OK — {total} linhas em {n_tenants} tenants."))
