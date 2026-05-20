"""T-CLI-104 — avalia o circuit breaker observado de `AcessoDadosCliente`.

Sliding window 5min + threshold OR:
  (pct >= 0.1% AND total >= 1000) OR (falhas_absolutas >= 3 em 5min)

Tenants violando o limiar geram evento P1 imutavel
`sistema.breaker_acesso_pii.disparado` na cadeia hash F-A
(via `publicar_evento`). Idempotente por janela: `causation_id` =
uuid5(NAMESPACE, f"breaker:{tenant_id}:{janela_truncada_5min}") →
UNIQUE `(causation_id, acao)` no `bus_outbox` dedupa multi-execuções.

Wave A pluga este comando em cron Procrastinate. Marco 1 invoca
manual / drill.

Uso:
    docker compose exec app poetry run python manage.py avaliar_circuit_breaker_acesso_pii
"""

from __future__ import annotations

import uuid
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.multitenant.connection import run_as_system

_NAMESPACE_BREAKER = uuid.UUID("550e8400-e29b-41d4-a716-446655440104")  # T-CLI-104


class Command(BaseCommand):
    help = (
        "Avalia o circuit breaker observado de AcessoDadosCliente. "
        "Dispara evento P1 na cadeia F-A pra tenants violando o limiar."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        # SELECT cross-tenant exige modo_sistema (RLS permite com TRUE).
        with run_as_system():
            with connection.cursor() as cur:
                # Sliding window: últimos 5 min. Janela bucket truncada
                # serve apenas como CHAVE DE IDEMPOTÊNCIA do evento P1
                # (causation_id determinístico).
                cur.execute(
                    """
                    SELECT
                        tenant_id,
                        COUNT(*) FILTER (WHERE NOT ok) AS falhas,
                        COUNT(*) AS total,
                        date_trunc('minute', now())
                            - interval '1 min'
                              * mod(extract(minute from now())::int, 5)
                            AS janela_inicio
                    FROM breaker_acesso_pii_evento
                    WHERE ts >= now() - interval '5 minutes'
                    GROUP BY tenant_id
                    HAVING (
                        COUNT(*) FILTER (WHERE NOT ok) >= 3
                        OR (
                            COUNT(*) >= 1000
                            AND COUNT(*) FILTER (WHERE NOT ok) * 1000
                                >= COUNT(*)
                        )
                    )
                    """
                )
                violadores = cur.fetchall()

        if not violadores:
            self.stdout.write(self.style.SUCCESS("nenhum tenant violando."))
            return

        for tenant_id, falhas, total, janela_inicio in violadores:
            chave_idemp = f"breaker:{tenant_id}:{janela_inicio.isoformat()}"
            cid = uuid.uuid5(_NAMESPACE_BREAKER, chave_idemp)
            # Idempotência (MÉDIO T4 tech-lead): checar se evento P1 com
            # esse causation_id já existe na cadeia F-A. `publicar_evento`
            # garante idempotência apenas no `bus_outbox` (UNIQUE
            # causation_id+acao); a cadeia hash F-A é append-only sem
            # UNIQUE, então a checagem precisa ser explícita aqui.
            # Em Marco 1 commands rodam serial (cron único Wave A) — sem
            # race; pré-1º tenant pago, advisory lock cobre se necessário.
            with run_as_system():
                with connection.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM auditoria "
                        "WHERE action = %s "
                        "AND payload_jsonb->>'causation_id' = %s "
                        "LIMIT 1",
                        ["sistema.breaker_acesso_pii.disparado", str(cid)],
                    )
                    ja_disparou = cur.fetchone() is not None
                if ja_disparou:
                    self.stdout.write(
                        f"P1 ja disparado nesta janela (idempotente): "
                        f"tenant={tenant_id} cid={cid}"
                    )
                    continue
                publicar_evento(
                    acao="sistema.breaker_acesso_pii.disparado",
                    payload={
                        "causation_id": str(cid),  # idempotência on-chain
                        "tenant_id": str(tenant_id),
                        "falhas": int(falhas),
                        "total": int(total),
                        "pct": float(falhas) * 100 / float(total) if total else 0,
                        "janela_inicio": janela_inicio.isoformat(),
                    },
                    causation_id=cid,
                    tenant_id=None,
                    resource_summary=f"tenant={tenant_id} {falhas}/{total}",
                )
            self.stdout.write(
                self.style.WARNING(
                    f"P1 disparado: tenant={tenant_id} "
                    f"falhas={falhas}/total={total} janela={janela_inicio}"
                )
            )
