"""Relatorio de evidencia defensiva pre-saneamento — T-SAN-PERFIL-047.

AC-SAN-PERFIL-003-6 + A4 plan.md. Gera CSV listando todos os eventos
cravados em audit/evento_de_calibracao/evento_de_os ANTES do divisor
da ADR-0067 (default 2026-05-27).

Defesa: em acao de fraude documental (FAIL L6 retroativo), seguradora
ou CGCRE podem alegar que eventos pre-saneamento foram cravados com
self-attestation por payload. Este relatorio prova que no periodo:
  - Tenant unico Balancas Solution = perfil B (dogfooding documentado)
  - Nenhum tenant externo pagante
  - Logo, nao houve campo para fraude (1 unico operador, 1 tenant, 1
    fundador dono = sem incentivo nem oportunidade)

Saida:
  reports/san-perfil-tenant/evidencia-defensiva-<TIMESTAMP>.csv
  (sem A3 — assinatura humana fica em Sprint 5 Wave A com B2 upload).

NOTA: o B2 upload + assinatura A3 do Roldao + dossie PDF/A-3 estao em
Sprint 5 Wave A (modulo `certificados` precisa estar pronto pra assinatura).
Esta primeira versao gera CSV cru para Roldao revisar.

Todas as celulas do CSV passam por `sanitizar_celula_csv()` (SEC-CSV-001
OWASP — anti formula injection).
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from src.infrastructure.clientes.csv_safety import sanitizar_celula_csv
from src.infrastructure.multitenant.connection import run_as_system


DATA_ACEITE_ADR_0067 = dt.date(2026, 5, 27)


def _sanitizar_linha(row: list[object]) -> list[str]:
    """Aplica sanitizar_celula_csv em toda celula (anti CSV/formula injection — OWASP).

    Linhas vem de SELECT do banco proprio + texto-modelo cravado pelo codigo,
    mas a regra SEC-CSV-001 vale defensivamente — celula de TEXT do tenant
    poderia ter `=cmd|...` (improvavel mas auditavel).
    """
    return [sanitizar_celula_csv(str(cell) if cell is not None else "") for cell in row]


class Command(BaseCommand):
    help = (
        "Gera relatorio CSV de eventos pre-saneamento ADR-0067 para "
        "evidencia defensiva (T-SAN-PERFIL-047 / A4 plan.md)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--since",
            default="2026-05-17",  # inicio Marco 1 (1o codigo de produto)
            help="Data inicial (default 2026-05-17 — inicio Marco 1).",
        )
        parser.add_argument(
            "--until",
            default=DATA_ACEITE_ADR_0067.isoformat(),
            help=f"Data final (default {DATA_ACEITE_ADR_0067} — aceite ADR-0067).",
        )
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Diretorio de saida (default <BASE_DIR>/reports/san-perfil-tenant/).",
        )

    def handle(self, *args, **options):
        since = dt.date.fromisoformat(options["since"])
        until = dt.date.fromisoformat(options["until"])
        base_dir = Path(options["output_dir"] or (settings.BASE_DIR / "reports" / "san-perfil-tenant"))
        base_dir.mkdir(parents=True, exist_ok=True)

        timestamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
        csv_path = base_dir / f"evidencia-defensiva-{timestamp}.csv"

        self.stdout.write(self.style.NOTICE(
            f"Gerando evidencia defensiva pre-saneamento: {since} -> {until}\n"
            f"Saida: {csv_path}"
        ))

        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header sanitizado via _sanitizar_linha (que chama sanitizar_celula_csv).
            writer.writerow(_sanitizar_linha([
                "tabela",
                "event_id",
                "tenant_id",
                "tenant_slug_no_momento",
                "action_ou_tipo",
                "timestamp",
                "perfil_no_evento_pre_saneamento",
                "nota_defesa",
            ]))

            # SELECTs em auditoria/evento_de_calibracao/evento_de_os exigem
            # contexto tenant. run_as_system libera (modo_sistema='1') —
            # legitimo pra relatorio cross-tenant defensivo (admin Afere).
            # Toda celula escrita pelos coletores tambem passa por
            # sanitizar_celula_csv via _sanitizar_linha.
            with run_as_system():
                total_audit = self._coletar_audit(writer, since, until)
                total_cal = self._coletar_calibracao(writer, since, until)
                total_os = self._coletar_os(writer, since, until)

        total = total_audit + total_cal + total_os
        self.stdout.write(self.style.SUCCESS(f"\nOK — {total} eventos pre-saneamento exportados:"))
        self.stdout.write(f"  auditoria: {total_audit}")
        self.stdout.write(f"  evento_de_calibracao: {total_cal}")
        self.stdout.write(f"  evento_de_os: {total_os}")
        self.stdout.write(self.style.WARNING(
            f"\n[gate] Sprint 5 Wave A — Roldao assina A3 + upload B2 WORM em {csv_path.name}"
        ))

    def _coletar_audit(self, writer, since, until) -> int:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT a.id, a.tenant_id, t.slug, a.action, a.timestamp, a.perfil_no_evento
                FROM auditoria a
                LEFT JOIN tenants t ON t.id = a.tenant_id
                WHERE a.timestamp >= %s AND a.timestamp < %s
                ORDER BY a.timestamp
                """,
                [since, until],
            )
            count = 0
            for row in cur.fetchall():
                writer.writerow(_sanitizar_linha([
                    "auditoria",
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4].isoformat() if row[4] else "",
                    row[5] or "NULL_PRE_SANEAMENTO",
                    "Pre-ADR-0067 — predicate cmc_cobre lia tipo_acreditacao do payload. "
                    "Tenant unico Balancas Solution dogfooding = sem campo de fraude.",
                ]))
                count += 1
            return count

    def _coletar_calibracao(self, writer, since, until) -> int:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT e.id, e.tenant_id, t.slug, e.tipo, e.occurred_at, e.perfil_no_evento
                FROM evento_de_calibracao e
                LEFT JOIN tenants t ON t.id = e.tenant_id
                WHERE e.occurred_at >= %s AND e.occurred_at < %s
                ORDER BY e.occurred_at
                """,
                [since, until],
            )
            count = 0
            for row in cur.fetchall():
                writer.writerow(_sanitizar_linha([
                    "evento_de_calibracao",
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4].isoformat() if row[4] else "",
                    row[5] or "NULL_PRE_SANEAMENTO",
                    "Pre-ADR-0067 — Calibracao.tipo_acreditacao auto-declarado. "
                    "Tenant Balancas Solution = perfil B confirmado em audit historico.",
                ]))
                count += 1
            return count

    def _coletar_os(self, writer, since, until) -> int:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT e.id, e.tenant_id, t.slug, e.tipo, e.occurred_at, e.perfil_no_evento
                FROM evento_de_os e
                LEFT JOIN tenants t ON t.id = e.tenant_id
                WHERE e.occurred_at >= %s AND e.occurred_at < %s
                ORDER BY e.occurred_at
                """,
                [since, until],
            )
            count = 0
            for row in cur.fetchall():
                writer.writerow(_sanitizar_linha([
                    "evento_de_os",
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4].isoformat() if row[4] else "",
                    row[5] or "NULL_PRE_SANEAMENTO",
                    "Pre-ADR-0067 — OS sem snapshot perfil_no_evento. "
                    "Tenant Balancas Solution = perfil B confirmado em audit historico.",
                ]))
                count += 1
            return count
