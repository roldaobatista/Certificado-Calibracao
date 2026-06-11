"""T-PPS-042 (ADV-PPS-06) — TTL 90d do staging de importação CSV.

Elimina lotes (`importacao_catalogo` + linhas em cascata) criados há mais de
90 dias — linhas rejeitadas/abandonadas saem; aceitas já viraram item de
catálogo (a prova permanente é o SHA-256 no evento WORM
`Catalogo.ImportacaoConcluida`, não o staging). IDEMPOTENTE: reexecução
diária não tem efeito além do corte.

Uso:
    python manage.py limpar_importacoes_expiradas [--tenant <uuid>] [--dias 90]
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from src.infrastructure.multitenant.jobs import (
    iter_tenants_ativos,
    processar_em_contexto_tenant,
)
from src.infrastructure.produtos_pecas_servicos.repositories import (
    DjangoImportacaoCatalogoRepository,
)
from src.infrastructure.tenant.models import Tenant

logger = logging.getLogger(__name__)

TTL_DIAS_DEFAULT = 90


class Command(BaseCommand):
    help = (
        "Elimina importações de catálogo em staging com mais de 90 dias "
        "(TTL ADV-PPS-06; idempotente)."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--tenant", type=str, help="Processa apenas o tenant_id especificado (UUID)."
        )
        parser.add_argument(
            "--dias",
            type=int,
            default=TTL_DIAS_DEFAULT,
            help=f"Janela de retenção em dias (default {TTL_DIAS_DEFAULT}).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        tenant_id_filtro = options.get("tenant")
        dias = options["dias"]
        if dias < 1:
            raise CommandError("--dias deve ser >= 1.")
        limite = timezone.now() - timedelta(days=dias)

        if tenant_id_filtro:
            try:
                tenants = [Tenant.objects.get(id=UUID(tenant_id_filtro))]
            except (Tenant.DoesNotExist, ValueError) as exc:
                raise CommandError(f"tenant invalido: {exc}") from exc
        else:
            tenants = list(iter_tenants_ativos())

        repo = DjangoImportacaoCatalogoRepository()

        def _limpar(tenant: Tenant) -> int:
            return repo.eliminar_importacoes_anteriores_a(
                tenant_id=tenant.id, limite=limite
            )

        resultados = processar_em_contexto_tenant(_limpar, tenants=tenants)
        total = sum(resultados.values())
        for tenant_id, n in resultados.items():
            if n:
                self.stdout.write(f"[{tenant_id}] {n} lote(s) eliminado(s).")
                # P9 OBS-B4: rastro estruturado da execucao da matriz de
                # retencao (ADV-PPS-06) — stdout de cron e efemero.
                logger.info(
                    "staging de importacao expirado eliminado",
                    extra={
                        "tenant_id": str(tenant_id),
                        "lotes": n,
                        "corte": limite.isoformat(),
                    },
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Processados {len(tenants)} tenant(s); {total} lote(s) de staging "
                f"eliminado(s) (corte {limite.isoformat()})."
            )
        )
