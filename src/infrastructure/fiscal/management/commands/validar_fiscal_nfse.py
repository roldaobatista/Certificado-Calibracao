"""Drill `validar_fiscal_nfse` (frente NFS-e Fatia 1b, estrutural).

Verifica que migrations + RLS + triggers WORM + grants + UNIQUE de negócio da
tabela `nota_fiscal_servico` foram aplicados. Roda após migrate. Espelha o molde
`validar_escopos_cmc` (DrillResult). Cobre o verificável por introspecção PG:
  1. tabela existe
  2. RLS ENABLED (INV-TENANT-001)
  3. RLS FORCE (NOBYPASSRLS — ADR-0002 / INV-TENANT-002)
  4. >=4 policies RLS (migration 0002 pattern v2)
  5. UNIQUE de negócio (tenant, origem_id, versao) — INV-FIS-005
  6. 2 triggers WORM Padrão B (block-delete + worm-check; migration 0003)
  7. app_user tem SELECT/INSERT/UPDATE/DELETE (migration 0004)

O comportamento PG real (RLS cross-tenant + WORM) é coberto por
tests/test_fiscal_schema_fatia1b.py.

Uso:
    docker compose exec app poetry run python manage.py validar_fiscal_nfse
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand
from django.db import connection

TABELA = "nota_fiscal_servico"
TRIGGERS_WORM = (
    "nota_fiscal_servico_block_delete_trg",
    "nota_fiscal_servico_worm_check_trg",
)
UNIQUE_NEGOCIO = "uq_nfse_origem_versao"
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
        # 1. tabela existe
        cur.execute(
            "SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename=%s", [TABELA]
        )
        existe = cur.fetchone() is not None
        res.append(DrillResult(f"tabela {TABELA} existe", existe, "" if existe else "AUSENTE"))
        if not existe:
            return res

        # 2/3. RLS enabled + forced
        cur.execute(
            "SELECT c.relrowsecurity, c.relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relname=%s",
            [TABELA],
        )
        row = cur.fetchone()
        enabled, forced = (bool(row[0]), bool(row[1])) if row else (False, False)
        res.append(DrillResult(f"RLS ENABLED em {TABELA}", enabled))
        res.append(DrillResult(f"RLS FORCE em {TABELA}", forced))

        # 4. >=4 policies
        cur.execute("SELECT count(*) FROM pg_policies WHERE tablename=%s", [TABELA])
        n_pol = cur.fetchone()[0]
        res.append(DrillResult(f">=4 policies RLS em {TABELA}", n_pol >= 4, f"{n_pol} policies"))

        # 5. UNIQUE de negócio
        cur.execute(
            "SELECT 1 FROM pg_constraint WHERE conname=%s AND contype='u'", [UNIQUE_NEGOCIO]
        )
        uq = cur.fetchone() is not None
        res.append(DrillResult(f"UNIQUE {UNIQUE_NEGOCIO} (INV-FIS-005)", uq))

        # 6. triggers WORM
        cur.execute(
            "SELECT tgname FROM pg_trigger WHERE tgrelid=%s::regclass AND NOT tgisinternal",
            [TABELA],
        )
        triggers = {r[0] for r in cur.fetchall()}
        for t in TRIGGERS_WORM:
            res.append(DrillResult(f"trigger WORM {t}", t in triggers))

        # 7. grants app_user
        cur.execute(
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE table_name=%s AND grantee='app_user'",
            [TABELA],
        )
        privs = {r[0] for r in cur.fetchall()}
        for p in _PRIVILEGIOS:
            res.append(DrillResult(f"app_user {p} em {TABELA}", p in privs))
    return res


class Command(BaseCommand):
    help = "Drill estrutural da tabela fiscal nota_fiscal_servico (Fatia 1b)."

    def handle(self, *args: object, **options: object) -> None:
        resultados = _verificar()
        self.stdout.write("== validar_fiscal_nfse ==")
        for r in resultados:
            self.stdout.write(str(r))
        falhas = [r for r in resultados if not r.passou]
        total = len(resultados)
        ok = total - len(falhas)
        self.stdout.write(f"\n{ok}/{total} checks PASS")
        if falhas:
            sys.exit(1)
