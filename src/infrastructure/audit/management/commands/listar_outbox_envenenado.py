"""Lista linhas do `bus_outbox` envenenadas (tentativas >= 5).

Atende BLOQ-B do tech-lead (dead-letter logica) + parte de BLOQ-A7 do
advogado (DPO inspeciona fila envenenada sem expor `envelope_jsonb` —
defesa em profundidade contra PII).

NUNCA exibe `envelope_jsonb`. Wave A entrega endpoint REST
`/dpo/outbox-quarentena` com AuthorizationProvider (perfil dedicado).

Uso:
    docker compose exec app poetry run python manage.py listar_outbox_envenenado
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

from src.infrastructure.multitenant.connection import run_as_system


class Command(BaseCommand):
    help = (
        "Lista linhas do bus_outbox com tentativas >= 5 (poison messages). "
        "NUNCA mostra envelope_jsonb (BLOQ-A7 advogado)."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        with run_as_system():
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT id, causation_id, acao, tenant_id, "
                    "tentativas, ultimo_erro, criado_em, processado_em "
                    "FROM bus_outbox "
                    "WHERE tentativas >= 5 AND processado_em IS NULL "
                    "ORDER BY criado_em"
                )
                rows = cur.fetchall()
        if not rows:
            self.stdout.write(self.style.SUCCESS("nenhuma linha envenenada."))
            return
        self.stdout.write(self.style.WARNING(f"{len(rows)} linha(s) envenenada(s):"))
        for id_, cid, acao, tid, tent, erro, criado, _proc in rows:
            self.stdout.write(
                f"  id={id_} causation_id={cid} acao={acao} tenant={tid} "
                f"tentativas={tent} criado_em={criado}"
            )
            if erro:
                self.stdout.write(f"    ultimo_erro: {erro}")
