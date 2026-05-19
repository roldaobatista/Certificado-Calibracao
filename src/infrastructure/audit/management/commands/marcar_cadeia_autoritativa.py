"""T-FA-02 / AC-FA-005-6 — marco de corte da cadeia autoritativa.

Revisão RBC (C2-a): a fronteira entre cadeia pré-Foundation
(não-autoritativa cronologicamente — `sequencia` é ordem heap nas linhas
criadas antes da migration que adicionou a coluna) e cadeia autoritativa
**não pode ser uma frase em doc** — em supervisão CGCRE, alegação verbal
sobre integridade de registro é não-conformidade. Tem que ser um **elo
imutável gravado dentro da própria trilha**, encadeado como qualquer
outro (logo: à prova de adulteração + verificável por recomputo).

Uso (idempotente — rodar uma vez ao fechar F-A):
    docker compose exec app poetry run python manage.py \
        marcar_cadeia_autoritativa

Idempotência: se o marco já existe na cadeia sistema, não duplica.
Usa a FONTE ÚNICA de hash (`registrar_auditoria`) — o marco é um elo
normal da cadeia sistema (sob run_as_system), não SQL cru paralelo.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db.models import Max

ACTION_MARCO = "auditoria.marco_inicio_cadeia_autoritativa"


class Command(BaseCommand):
    help = "Grava (idempotente) o marco de corte da cadeia autoritativa F-A."

    def handle(self, *args: Any, **opts: Any) -> None:
        from src.infrastructure.audit.models import Auditoria
        from src.infrastructure.audit.services import registrar_auditoria
        from src.infrastructure.multitenant.connection import run_as_system

        with run_as_system():
            ja_existe = Auditoria.objects.filter(
                tenant_id__isnull=True, action=ACTION_MARCO
            ).exists()
            if ja_existe:
                self.stdout.write(
                    self.style.WARNING(
                        "Marco de corte já existe na cadeia sistema — "
                        "idempotente, nada a fazer."
                    )
                )
                return

            corte = (
                Auditoria.objects.aggregate(m=Max("sequencia"))["m"] or 0
            )
            elo = registrar_auditoria(
                tenant_id=None,
                usuario_id=None,
                action=ACTION_MARCO,
                resource_summary="fronteira Foundation F-A",
                payload={
                    "sequencia_corte": corte,
                    "motivo": (
                        "Elos com sequencia <= sequencia_corte sao "
                        "pre-Foundation: ordem fisica de heap, NAO "
                        "cronologicamente autoritativos. Integridade "
                        "criptografica (hash chain) preservada para todos. "
                        "Elos com sequencia > corte sao autoritativos "
                        "(AC-FA-005-6 / RBC C2-a)."
                    ),
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Marco gravado na cadeia sistema (sequencia_corte={corte}, "
                f"elo id={elo.id}). Imutável + encadeado."
            )
        )
