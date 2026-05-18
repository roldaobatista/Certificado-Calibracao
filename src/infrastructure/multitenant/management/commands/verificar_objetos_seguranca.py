"""Command: confere que objetos de segurança existem no banco (FA-A4).

Roda no drill F-A e pode rodar pós-deploy. Exit 1 se algum objeto de
segurança (RLS/policy/trigger/função) que uma migration deveria ter
criado NÃO está no catálogo real do Postgres — pega o caso "migrate
reportou OK sem aplicar".

Uso:
    docker compose exec app poetry run python manage.py verificar_objetos_seguranca
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand

from src.infrastructure.multitenant.verificacao_objetos import (
    verificar_objetos_seguranca,
)


class Command(BaseCommand):
    help = "Verifica que RLS/policies/triggers/funcoes de seguranca existem no banco."

    def handle(self, *args, **options):
        problemas = verificar_objetos_seguranca()
        if not problemas:
            self.stdout.write(
                self.style.SUCCESS(
                    "OK — todos os objetos de seguranca existem no banco "
                    "(nenhuma migration mentiu)."
                )
            )
            return
        self.stdout.write(
            self.style.ERROR(
                f"FALHA — {len(problemas)} objeto(s) de seguranca ausente(s):"
            )
        )
        for p in problemas:
            self.stdout.write(self.style.ERROR(f"  - {p}"))
        sys.exit(1)
