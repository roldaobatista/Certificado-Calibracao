"""Drill ``validar_agenda`` (frente agenda Fatia 1b, estrutural).

Verifica que migrations + RLS + triggers WORM + EXCLUDE GIST + UNIQUE + grants
das tabelas agenda foram aplicados. Roda após migrate. Espelha o molde
``validar_contas_receber`` (DrillResult). Cobre o verificável por introspecção PG:

Para cada tabela (7 total):
  1. tabela existe
  2. RLS ENABLED (INV-TENANT-001)
  3. RLS FORCE (NOBYPASSRLS — ADR-0002 / INV-TENANT-002)
  4. >=4 policies RLS (migration 0002 pattern v2)
  5. app_user tem SELECT/INSERT/UPDATE/DELETE (migration 0005)

Adicionalmente:
  6. EXCLUDE GIST ``excl_agenda_tecnico_overlap`` em evento_agenda (R1/R12 — INV-AG-OVERLAP-001)
  7. CHECK ``chk_agenda_evento_atividade_obrigatoria_quando_os`` (INV-AG-ATIVIDADE-001)
  8. UNIQUE ``uq_agenda_evento_recorrencia_ocorrencia`` (R10 — INV-AG-RECORRENCIA-001)
  9. Triggers WORM INSERT-only: evento_auditoria_agenda (block-update + block-delete)
 10. Triggers WORM INSERT-only: registro_no_show (block-update + block-delete)
 11. Triggers WORM INSERT-only: regime_jornada_colaborador (block-update + block-delete)

O comportamento PG real (RLS cross-tenant + WORM + EXCLUDE) é coberto por
tests/test_agenda_schema_fatia1b.py.

Uso:
    docker compose exec app poetry run python manage.py validar_agenda
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand
from django.db import connection

_TABELAS_RLS = [
    "evento_agenda",
    "recorrencia_agenda",
    "registro_no_show",
    "capacidade_tecnico",
    "feriado",
    "evento_auditoria_agenda",
    "regime_jornada_colaborador",
]

_TRIGGERS_AUDITORIA = (
    "evento_auditoria_agenda_block_update_trg",
    "evento_auditoria_agenda_block_delete_trg",
)
_TRIGGERS_NOSHOW = (
    "registro_no_show_block_update_trg",
    "registro_no_show_block_delete_trg",
)
_TRIGGERS_REGIME = (
    "regime_jornada_colaborador_block_update_trg",
    "regime_jornada_colaborador_block_delete_trg",
)

_EXCLUDE_OVERLAP = "excl_agenda_tecnico_overlap"
_CHECK_ATIVIDADE = "chk_agenda_evento_atividade_obrigatoria_quando_os"
# UniqueConstraint com condition= vira partial index no PG (não pg_constraint contype='u')
_UNIQUE_RECORRENCIA = "uq_agenda_evento_recorrencia_ocorrencia"
_PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE")


class DrillResult:
    def __init__(self, nome: str, passou: bool, detalhe: str = "") -> None:
        self.nome = nome
        self.passou = passou
        self.detalhe = detalhe

    def __str__(self) -> str:
        marca = "PASS" if self.passou else "FAIL"
        return f"  [{marca}] {self.nome}" + (f" — {self.detalhe}" if self.detalhe else "")


def _verificar() -> list[DrillResult]:
    res: list[DrillResult] = []
    with connection.cursor() as cur:
        # === RLS + grants por tabela ===
        for tabela in _TABELAS_RLS:
            # 1. tabela existe
            cur.execute(
                "SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename=%s",
                [tabela],
            )
            existe = cur.fetchone() is not None
            res.append(DrillResult(f"tabela {tabela} existe", existe))
            if not existe:
                continue

            # 2/3. RLS enabled + forced
            cur.execute(
                "SELECT c.relrowsecurity, c.relforcerowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='public' AND c.relname=%s",
                [tabela],
            )
            row = cur.fetchone()
            enabled, forced = (bool(row[0]), bool(row[1])) if row else (False, False)
            res.append(DrillResult(f"RLS ENABLED em {tabela}", enabled))
            res.append(DrillResult(f"RLS FORCE em {tabela}", forced))

            # 4. >=4 policies
            cur.execute("SELECT count(*) FROM pg_policies WHERE tablename=%s", [tabela])
            n_pol = cur.fetchone()[0]
            res.append(
                DrillResult(f">=4 policies RLS em {tabela}", n_pol >= 4, f"{n_pol} policies")
            )

            # 5. grants app_user
            cur.execute(
                "SELECT privilege_type FROM information_schema.role_table_grants "
                "WHERE table_name=%s AND grantee='app_user'",
                [tabela],
            )
            privs = {r[0] for r in cur.fetchall()}
            for p in _PRIVILEGIOS:
                res.append(DrillResult(f"app_user {p} em {tabela}", p in privs))

        # === EXCLUDE GIST de overlap em evento_agenda ===
        cur.execute(
            "SELECT 1 FROM pg_constraint "
            "WHERE conname=%s AND contype='x' AND conrelid='evento_agenda'::regclass",
            [_EXCLUDE_OVERLAP],
        )
        res.append(
            DrillResult(
                f"EXCLUDE GIST {_EXCLUDE_OVERLAP} (INV-AG-OVERLAP-001)",
                cur.fetchone() is not None,
            )
        )

        # === CHECK atividade_id quando tipo='os' ===
        cur.execute(
            "SELECT 1 FROM pg_constraint WHERE conname=%s AND contype='c'",
            [_CHECK_ATIVIDADE],
        )
        res.append(
            DrillResult(
                f"CHECK {_CHECK_ATIVIDADE} (INV-AG-ATIVIDADE-001)",
                cur.fetchone() is not None,
            )
        )

        # === UNIQUE recorrencia (partial index) ===
        cur.execute(
            "SELECT 1 FROM pg_indexes WHERE indexname=%s AND schemaname='public'",
            [_UNIQUE_RECORRENCIA],
        )
        res.append(
            DrillResult(
                f"UNIQUE {_UNIQUE_RECORRENCIA} (INV-AG-RECORRENCIA-001)",
                cur.fetchone() is not None,
            )
        )

        # === Triggers WORM evento_auditoria_agenda ===
        cur.execute(
            "SELECT tgname FROM pg_trigger "
            "WHERE tgrelid='evento_auditoria_agenda'::regclass AND NOT tgisinternal",
        )
        trg_audit = {r[0] for r in cur.fetchall()}
        for t in _TRIGGERS_AUDITORIA:
            res.append(DrillResult(f"trigger {t}", t in trg_audit))

        # === Triggers INSERT-only registro_no_show ===
        cur.execute(
            "SELECT tgname FROM pg_trigger "
            "WHERE tgrelid='registro_no_show'::regclass AND NOT tgisinternal",
        )
        trg_noshow = {r[0] for r in cur.fetchall()}
        for t in _TRIGGERS_NOSHOW:
            res.append(DrillResult(f"trigger {t}", t in trg_noshow))

        # === Triggers INSERT-only regime_jornada_colaborador ===
        cur.execute(
            "SELECT tgname FROM pg_trigger "
            "WHERE tgrelid='regime_jornada_colaborador'::regclass AND NOT tgisinternal",
        )
        trg_regime = {r[0] for r in cur.fetchall()}
        for t in _TRIGGERS_REGIME:
            res.append(DrillResult(f"trigger {t}", t in trg_regime))

    return res


class Command(BaseCommand):
    help = "Drill estrutural das tabelas agenda (Fatia 1b — T-AGE-027)."

    def handle(self, *args: object, **options: object) -> None:
        resultados = _verificar()
        self.stdout.write("== validar_agenda ==")
        for r in resultados:
            self.stdout.write(str(r))
        falhas = [r for r in resultados if not r.passou]
        total = len(resultados)
        ok = total - len(falhas)
        self.stdout.write(f"\n{ok}/{total} checks PASS")
        if falhas:
            sys.exit(1)
