"""Management command: itera InadimplenciaSource e bloqueia clientes inadimplentes.

US-CLI-004 — AC-CLI-004-3 (job D+90). Marco 1: comando on-demand consumindo
mock (`MockInadimplenciaSource`). Wave A do `financeiro/contas-receber`
substitui o source + agenda no Procrastinate (cron 02:00 BRT).

R3 advogado: NAO bloqueia se `Tenant.bloqueio_automatico_inadimplencia_habilitado=False`
(default no Marco 1). Régua D+30/60/89 (AC-5) entra Wave A via `comunicacao-omnichannel`.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.core.management.base import BaseCommand

from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.clientes.bloqueio import (
    CAUSATION_TITULO_VENCIDO,
    MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
)
from src.infrastructure.clientes.inadimplencia import get_source
from src.infrastructure.clientes.models import Cliente, ClienteBloqueio
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.tenant.models import Tenant


class Command(BaseCommand):
    help = (
        "Itera InadimplenciaSource (mock no Marco 1) e bloqueia clientes "
        "inadimplentes >=90d, respeitando flag bloqueio_automatico_inadimplencia_habilitado."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="So lista o que faria, nao escreve.",
        )

    def handle(self, *args: Any, **opts: Any) -> None:
        dry = opts.get("dry_run", False)
        source = get_source()
        contadores = {"avaliados": 0, "bloqueados": 0, "skip_flag_off": 0, "skip_ja_bloqueado": 0}

        for item in source.iter_inadimplentes_90d():
            contadores["avaliados"] += 1
            try:
                tenant = Tenant.objects.get(id=item.tenant_id)
            except Tenant.DoesNotExist:
                continue
            if not tenant.bloqueio_automatico_inadimplencia_habilitado:
                contadores["skip_flag_off"] += 1
                continue

            with run_in_tenant_context(tenant.id):
                try:
                    cliente = Cliente.objects.get(id=item.cliente_id)
                except Cliente.DoesNotExist:
                    continue

                ativo = ClienteBloqueio.objects.filter(
                    cliente=cliente, desbloqueado_em__isnull=True
                ).first()
                if ativo is not None:
                    contadores["skip_ja_bloqueado"] += 1
                    continue

                if dry:
                    contadores["bloqueados"] += 1
                    self.stdout.write(f"[DRY] bloquearia cliente {cliente.id} tenant {tenant.id}")
                    continue

                from src.infrastructure.audit.services import registrar_auditoria

                justificativa = (
                    f"Bloqueio automatico — inadimplencia >=90 dias "
                    f"(dias_vencido={item.dias_vencido})"
                )
                bloqueio = ClienteBloqueio.objects.create(
                    cliente=cliente,
                    tenant=tenant,
                    motivo_categoria=MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
                    motivo_observacao="",
                    justificativa_bruta=justificativa,
                    causation_type=CAUSATION_TITULO_VENCIDO,
                    causation_id=item.causation_titulo_id,
                    confirmacao_comunicacao_previa=True,  # job presume régua já cumprida (Wave A valida)
                    bloqueado_por_usuario_id=None,
                )
                registrar_auditoria(
                    tenant_id=tenant.id,
                    usuario_id=None,
                    action="cliente.bloqueado",
                    resource_summary=str(cliente.id),
                    payload={
                        "event_id": str(uuid.uuid4()),
                        "cliente_id": str(cliente.id),
                        "tenant_id": str(tenant.id),
                        "bloqueio_id": str(bloqueio.id),
                        "motivo_categoria": MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
                        "justificativa_hash": hashear_pii_com_salt_tenant(justificativa, tenant.id),
                        "causation_type": CAUSATION_TITULO_VENCIDO,
                        "causation_id": str(item.causation_titulo_id),
                        "dias_vencido": item.dias_vencido,
                        "automatico": True,
                    },
                )
                contadores["bloqueados"] += 1

        self.stdout.write(self.style.SUCCESS(f"{contadores}"))
