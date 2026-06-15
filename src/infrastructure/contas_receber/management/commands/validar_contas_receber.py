"""Drill `validar_contas_receber` (frente contas-receber Fatia 1b, estrutural).

Verifica que migrations + RLS + triggers WORM + grants + UNIQUE de negócio das
tabelas contas-receber foram aplicados. Roda após migrate. Espelha o molde
`validar_fiscal_nfse` (DrillResult). Cobre o verificável por introspecção PG:

Para cada tabela:
  1. tabela existe
  2. RLS ENABLED (INV-TENANT-001)
  3. RLS FORCE (NOBYPASSRLS — ADR-0002 / INV-TENANT-002)
  4. >=4 policies RLS (migration 0002 pattern v2)
  5. app_user tem SELECT/INSERT/UPDATE/DELETE (migration 0004)

Adicionalmente:
  6. UNIQUE de negócio titulo_receber (uq_cr_titulo_os_ativo) — INV-CR-OS-TITULO-UNICO
  7. CHECK pix_recorrente+convenio (chk_cr_titulo_pix_recorrente_convenio) — INV-FIN-GW-002
  8. Triggers WORM titulo_receber (block-delete + worm-check)
  9. Triggers INSERT-only pagamento_titulo (block-update + block-delete)
 10. Triggers INSERT-only override_bloqueio (block-update + block-delete)
 11. Trigger perfil fallback titulo_receber (BEFORE INSERT — R4)

O comportamento PG real (RLS cross-tenant + WORM) é coberto por
tests/test_contas_receber_schema_fatia1b.py.

Uso:
    docker compose exec app poetry run python manage.py validar_contas_receber
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand
from django.db import connection

_TABELAS_RLS = [
    "titulo_receber",
    "parcela_titulo",
    "pagamento_titulo",
    "override_bloqueio",
]

_TRIGGERS_TITULO = (
    "titulo_receber_block_delete_trg",
    "titulo_receber_worm_check_trg",
    "titulo_receber_perfil_fallback_trg",
)
_TRIGGERS_PAGAMENTO = (
    "pagamento_titulo_block_update_trg",
    "pagamento_titulo_block_delete_trg",
)
_TRIGGERS_OVERRIDE = (
    "override_bloqueio_block_update_trg",
    "override_bloqueio_block_delete_trg",
)

_UNIQUE_TITULO = "uq_cr_titulo_os_ativo"
_CHECK_PIX = "chk_cr_titulo_pix_recorrente_convenio"
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

        # === UNIQUE / CHECK em titulo_receber ===
        # UniqueConstraint com condition= vira partial index no PG (pg_indexes),
        # nao entra em pg_constraint contype='u'. Verificamos por pg_indexes.
        cur.execute(
            "SELECT 1 FROM pg_indexes WHERE indexname=%s AND schemaname='public'",
            [_UNIQUE_TITULO],
        )
        res.append(
            DrillResult(
                f"UNIQUE {_UNIQUE_TITULO} (INV-CR-OS-TITULO-UNICO)",
                cur.fetchone() is not None,
            )
        )

        cur.execute(
            "SELECT 1 FROM pg_constraint WHERE conname=%s AND contype='c'",
            [_CHECK_PIX],
        )
        res.append(
            DrillResult(
                f"CHECK {_CHECK_PIX} (INV-FIN-GW-002)",
                cur.fetchone() is not None,
            )
        )

        # === Triggers WORM titulo_receber ===
        cur.execute(
            "SELECT tgname FROM pg_trigger WHERE tgrelid='titulo_receber'::regclass "
            "AND NOT tgisinternal",
        )
        trg_titulo = {r[0] for r in cur.fetchall()}
        for t in _TRIGGERS_TITULO:
            res.append(DrillResult(f"trigger {t}", t in trg_titulo))

        # === Triggers INSERT-only pagamento_titulo ===
        cur.execute(
            "SELECT tgname FROM pg_trigger WHERE tgrelid='pagamento_titulo'::regclass "
            "AND NOT tgisinternal",
        )
        trg_pag = {r[0] for r in cur.fetchall()}
        for t in _TRIGGERS_PAGAMENTO:
            res.append(DrillResult(f"trigger {t}", t in trg_pag))

        # === Triggers INSERT-only override_bloqueio ===
        cur.execute(
            "SELECT tgname FROM pg_trigger WHERE tgrelid='override_bloqueio'::regclass "
            "AND NOT tgisinternal",
        )
        trg_ov = {r[0] for r in cur.fetchall()}
        for t in _TRIGGERS_OVERRIDE:
            res.append(DrillResult(f"trigger {t}", t in trg_ov))

    return res


class Command(BaseCommand):
    help = "Drill estrutural das tabelas contas-receber (Fatia 1b — T-CR-026)."

    def handle(self, *args: object, **options: object) -> None:
        resultados = _verificar()
        self.stdout.write("== validar_contas_receber ==")
        for r in resultados:
            self.stdout.write(str(r))
        falhas = [r for r in resultados if not r.passou]
        total = len(resultados)
        ok = total - len(falhas)
        self.stdout.write(f"\n{ok}/{total} checks PASS")
        if falhas:
            sys.exit(1)
