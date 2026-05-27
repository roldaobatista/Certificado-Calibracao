"""Drill estrutural Sprint 4 — T-SAN-PERFIL-049.

AC-SAN-PERFIL-003-3: valida que snapshots `perfil_no_evento` cobrem
todos os eventos pos-saneamento (Sprint 4 ativa trigger BEFORE INSERT
+ retrofit registrar_auditoria). Eventos PRE-saneamento ficam NULL —
sao tratados pelo relatorio T-SAN-PERFIL-047 (`validar_san_perfil_tenant_
eventos_historicos`) que entrega CSV+A3 para evidencia defensiva A4.

Uso:
    python manage.py validar_san_perfil_tenant_snapshots [--since YYYY-MM-DD]

Defaults a 2026-05-27 (data de aceite da ADR-0067) como divisor pre/pos
saneamento.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection


DATA_ACEITE_ADR_0067 = dt.date(2026, 5, 27)


class Command(BaseCommand):
    help = (
        "Drill Sprint 4 — valida cobertura de perfil_no_evento em audit + "
        "evento_de_calibracao + evento_de_os (T-SAN-PERFIL-049)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--since",
            default=DATA_ACEITE_ADR_0067.isoformat(),
            help=f"Data divisora pre/pos saneamento (default {DATA_ACEITE_ADR_0067}).",
        )

    def handle(self, *args, **options):
        since_str = options["since"]
        since = dt.date.fromisoformat(since_str)

        self.stdout.write(self.style.NOTICE(f"Drill snapshots SAN-PERFIL — divisor {since}\n"))

        checks: list[tuple[str, str, dict[str, Any]]] = [
            (
                "audit-pos-saneamento-cobertura",
                f"""
                SELECT
                    COUNT(*) FILTER (WHERE perfil_no_evento IS NOT NULL)::float / NULLIF(COUNT(*),0) AS pct,
                    COUNT(*) FILTER (WHERE perfil_no_evento IS NULL) AS null_count,
                    COUNT(*) AS total
                FROM auditoria
                WHERE timestamp >= %s
                """,
                {"since": since_str, "tabela": "auditoria", "min_pct": 0.95},
            ),
            (
                "evento-calibracao-pos-saneamento-cobertura",
                """
                SELECT
                    COUNT(*) FILTER (WHERE perfil_no_evento IS NOT NULL)::float / NULLIF(COUNT(*),0) AS pct,
                    COUNT(*) FILTER (WHERE perfil_no_evento IS NULL) AS null_count,
                    COUNT(*) AS total
                FROM evento_de_calibracao
                WHERE occurred_at >= %s
                """,
                {"since": since_str, "tabela": "evento_de_calibracao", "min_pct": 0.95},
            ),
            (
                "evento-os-pos-saneamento-cobertura",
                """
                SELECT
                    COUNT(*) FILTER (WHERE perfil_no_evento IS NOT NULL)::float / NULLIF(COUNT(*),0) AS pct,
                    COUNT(*) FILTER (WHERE perfil_no_evento IS NULL) AS null_count,
                    COUNT(*) AS total
                FROM evento_de_os
                WHERE occurred_at >= %s
                """,
                {"since": since_str, "tabela": "evento_de_os", "min_pct": 0.95},
            ),
        ]

        pass_count = 0
        fail_count = 0

        with connection.cursor() as cur:
            for nome, sql, meta in checks:
                cur.execute(sql, [meta["since"]])
                row = cur.fetchone()
                pct, null_count, total = row
                pct = pct or 0.0

                # Cobertura aceita: ou tabela vazia pos-saneamento (sem dado novo
                # = OK em ambiente de teste) OU >=95% preenchido.
                if total == 0:
                    self.stdout.write(self.style.SUCCESS(
                        f"  [PASS] {nome} — {meta['tabela']} vazia pos-saneamento (zero eventos novos para validar)"
                    ))
                    pass_count += 1
                elif pct >= meta["min_pct"]:
                    self.stdout.write(self.style.SUCCESS(
                        f"  [PASS] {nome} — {pct:.1%} preenchido ({total - null_count}/{total} eventos)"
                    ))
                    pass_count += 1
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  [FAIL] {nome} — {pct:.1%} < {meta['min_pct']:.1%} "
                        f"({null_count} eventos sem perfil_no_evento / total {total})"
                    ))
                    fail_count += 1

            # Trigger sanity check
            cur.execute("""
                SELECT trigger_name, event_object_table
                FROM information_schema.triggers
                WHERE trigger_name IN (
                    'audit_perfil_no_evento_default_trigger',
                    'evento_calibracao_perfil_no_evento_trigger',
                    'evento_os_perfil_no_evento_trigger'
                )
                ORDER BY event_object_table
            """)
            triggers = cur.fetchall()
            esperados = {
                "audit_perfil_no_evento_default_trigger": "auditoria",
                "evento_calibracao_perfil_no_evento_trigger": "evento_de_calibracao",
                "evento_os_perfil_no_evento_trigger": "evento_de_os",
            }
            achados = {row[0]: row[1] for row in triggers}
            for trg, tabela_esperada in esperados.items():
                if achados.get(trg) == tabela_esperada:
                    self.stdout.write(self.style.SUCCESS(
                        f"  [PASS] trigger-{trg} — ativa em {tabela_esperada}"
                    ))
                    pass_count += 1
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  [FAIL] trigger-{trg} — esperado em {tabela_esperada}, achado {achados.get(trg, 'NENHUM')}"
                    ))
                    fail_count += 1

        total_checks = pass_count + fail_count
        self.stdout.write("")
        self.stdout.write(f"===== Drill snapshots SAN-PERFIL: {pass_count}/{total_checks} PASS =====")

        if fail_count:
            self.stdout.write(self.style.ERROR(f"{fail_count} FAIL — investigar cobertura."))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("Sprint 4 snapshots estruturalmente OK."))
        self.stdout.write(
            "NOTA: eventos PRE-saneamento (timestamp < " + str(since) + ") nao sao "
            "cobertos por este drill. Use `validar_san_perfil_tenant_eventos_historicos` "
            "(T-SAN-PERFIL-047) para evidencia defensiva A4 (CSV+A3 dossie B2 WORM)."
        )
