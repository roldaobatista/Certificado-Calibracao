"""Drena `bus_outbox` uma vez (T-CLI-107 + T-CLI-110).

Wave A pluga um cron Procrastinate que invoca `drenar_outbox()` em
loop. Marco 1 entrega este management command para invocacao manual
(dogfooding + drill F-A).

Uso:
    docker compose exec app poetry run python manage.py drenar_outbox_uma_vez
    docker compose exec app poetry run python manage.py drenar_outbox_uma_vez --limit 50
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from src.infrastructure.audit.outbox_worker import drenar_outbox


class Command(BaseCommand):
    help = "Drena o bus_outbox uma vez (tentativas < 5). Wave A pluga em cron."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximo de linhas a drenar nesta execucao (default: 100).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        limit = options["limit"]
        resultados = drenar_outbox(limit=limit)
        processadas = sum(1 for r in resultados if r.status == "processada")
        falhadas = sum(1 for r in resultados if r.status == "falhou")
        lockadas = sum(1 for r in resultados if r.status == "ja_processada_ou_lockada")
        self.stdout.write(
            self.style.SUCCESS(
                f"drenar_outbox: {len(resultados)} linhas tentadas "
                f"(processadas={processadas}, falhadas={falhadas}, "
                f"lockadas/ja_processadas={lockadas})."
            )
        )
        for r in resultados:
            if r.status == "falhou":
                self.stdout.write(self.style.WARNING(f"  linha {r.linha_id} falhou: {r.erro}"))
