"""T-ECMC-017 — drill `validar_escopos_cmc` (M6 Fatia 1b, estrutural).

Verifica que migrations + RLS + triggers WORM + grants do M6 metrologia/escopos-cmc
foram aplicados. Roda no banco após migrate. Espelha `validar_m5_padroes` (mesmo
molde DrillResult). Cobre só o verificável por introspecção de catálogo PG:
  1. 2 tabelas M6 existem
  2. RLS ENABLED nas 2 tabelas (INV-TENANT-001)
  3. RLS FORCE nas 2 tabelas (NOBYPASSRLS — ADR-0002 / INV-TENANT-002)
  4. >=4 policies RLS por tabela (migration 0002 pattern v2)
  5. UNIQUE chave natural em escopo_cmc (INV-ECMC-001)
  6. 2 triggers WORM Padrão B em escopo_cmc (migration 0003)
  7. índice parcial de cobertura com condição CONFIRMADO + revogado IS NULL (TL-C-11)
  8. app_user tem SELECT/INSERT/UPDATE/DELETE nas 2 tabelas (migration 0004)

GATE-ECMC-DRILL-LOCAL (PG real — comportamento dos triggers/RLS cross-tenant):
  -> tests/regressao/test_inv_ecmc_p2_schema_triggers.py.

Uso:
    docker compose exec app poetry run python manage.py validar_escopos_cmc
"""

from __future__ import annotations

import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

TABELAS_M6 = ["escopo_cmc", "escopo_extraido"]

# trigger_name -> tabela esperada (migration 0003_triggers_worm.py)
TRIGGERS_WORM = {
    "escopo_cmc_block_delete_trg": "escopo_cmc",
    "escopo_cmc_worm_check_trg": "escopo_cmc",
}

INDICE_COBERTURA = "ecmc_cobertura_idx"
INDICES_ESPERADOS = ("ecmc_cobertura_idx", "ecmc_tenant_gr_est_idx", "eextr_tenant_conf_idx")
_PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE")


class DrillResult:
    def __init__(self, nome: str, passou: bool, detalhe: str = "") -> None:
        self.nome = nome
        self.passou = passou
        self.detalhe = detalhe

    def __str__(self) -> str:
        marca = "PASS" if self.passou else "FAIL"
        return f"  [{marca}] {self.nome}" + (f" — {self.detalhe}" if self.detalhe else "")


def _verificar_tabelas_existem() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        existentes = {row[0] for row in cur.fetchall()}
    return [
        DrillResult(f"tabela {t} existe", passou=(t in existentes), detalhe="" if t in existentes else "AUSENTE")
        for t in TABELAS_M6
    ]


def _verificar_rls() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname = ANY(%s)
            """,
            [TABELAS_M6],
        )
        status = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
    resultados: list[DrillResult] = []
    for tab in TABELAS_M6:
        enabled, force = status.get(tab, (False, False))
        resultados.append(
            DrillResult(f"RLS ENABLED em {tab}", passou=bool(enabled), detalhe="" if enabled else "INV-TENANT-001")
        )
        resultados.append(
            DrillResult(f"RLS FORCE em {tab}", passou=bool(force), detalhe="" if force else "INV-TENANT-002")
        )
    return resultados


def _verificar_policies() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT tablename, COUNT(*) FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = ANY(%s) GROUP BY tablename",
            [TABELAS_M6],
        )
        counts = dict(cur.fetchall())
    return [
        DrillResult(
            f">=4 policies RLS em {tab} (achou {counts.get(tab, 0)})",
            passou=(counts.get(tab, 0) >= 4),
            detalhe="" if counts.get(tab, 0) >= 4 else "policies insuficientes",
        )
        for tab in TABELAS_M6
    ]


def _verificar_unique_chave_natural() -> DrillResult:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT indexdef FROM pg_indexes
            WHERE tablename = 'escopo_cmc' AND indexdef ILIKE '%UNIQUE%'
              AND indexdef ILIKE '%tenant_id%' AND indexdef ILIKE '%grandeza%'
              AND indexdef ILIKE '%faixa_min%' AND indexdef ILIKE '%versao%'
            """
        )
        ok = cur.fetchone() is not None
    return DrillResult(
        "UNIQUE chave natural escopo_cmc (INV-ECMC-001)",
        passou=ok,
        detalhe="" if ok else "indice UNIQUE composto AUSENTE",
    )


def _verificar_triggers_worm() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT trigger_name, event_object_table FROM information_schema.triggers "
            "WHERE trigger_name = ANY(%s)",
            [list(TRIGGERS_WORM.keys())],
        )
        encontrados = {row[0]: row[1] for row in cur.fetchall()}
    resultados: list[DrillResult] = []
    for trg, tab in TRIGGERS_WORM.items():
        real = encontrados.get(trg)
        resultados.append(
            DrillResult(
                f"trigger {trg} em {tab}",
                passou=(real == tab),
                detalhe="" if real == tab else f"AUSENTE/tabela errada (achou {real!r})",
            )
        )
    return resultados


def _verificar_indice_parcial() -> DrillResult:
    """Índice parcial de cobertura tem a condição CONFIRMADO + revogado IS NULL (TL-C-11)."""
    with connection.cursor() as cur:
        cur.execute("SELECT indexdef FROM pg_indexes WHERE indexname = %s", [INDICE_COBERTURA])
        row = cur.fetchone()
    indexdef = (row[0] if row else "") or ""
    ok = "WHERE" in indexdef.upper() and "CONFIRMADO" in indexdef and "revogado_em" in indexdef
    return DrillResult(
        f"indice parcial {INDICE_COBERTURA} com condicao CONFIRMADO (TL-C-11)",
        passou=ok,
        detalhe="" if ok else f"condicao parcial ausente: {indexdef!r}",
    )


def _verificar_indices_suporte() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute("SELECT indexname FROM pg_indexes WHERE tablename = ANY(%s)", [TABELAS_M6])
        existentes = {row[0] for row in cur.fetchall()}
    return [
        DrillResult(f"indice {idx} presente", passou=(idx in existentes), detalhe="" if idx in existentes else "AUSENTE")
        for idx in INDICES_ESPERADOS
    ]


def _verificar_grants_app_user() -> list[DrillResult]:
    resultados: list[DrillResult] = []
    with connection.cursor() as cur:
        for tab in TABELAS_M6:
            faltando = []
            for priv in _PRIVILEGIOS:
                cur.execute("SELECT has_table_privilege('app_user', %s, %s)", [tab, priv])
                if not cur.fetchone()[0]:
                    faltando.append(priv)
            resultados.append(
                DrillResult(
                    f"app_user tem {'/'.join(_PRIVILEGIOS)} em {tab}",
                    passou=not faltando,
                    detalhe="" if not faltando else f"faltando: {faltando}",
                )
            )
    return resultados


def rodar_todas_verificacoes() -> list[DrillResult]:
    resultados: list[DrillResult] = []
    resultados.extend(_verificar_tabelas_existem())
    resultados.extend(_verificar_rls())
    resultados.extend(_verificar_policies())
    resultados.append(_verificar_unique_chave_natural())
    resultados.extend(_verificar_triggers_worm())
    resultados.append(_verificar_indice_parcial())
    resultados.extend(_verificar_indices_suporte())
    resultados.extend(_verificar_grants_app_user())
    return resultados


class Command(BaseCommand):
    help = "Drill estrutural M6 escopos-cmc (T-ECMC-017) — verifica migrations/triggers/RLS."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("=" * 65)
        self.stdout.write("Drill validar_escopos_cmc — verificacoes estruturais")
        self.stdout.write("=" * 65)

        resultados = rodar_todas_verificacoes()
        passou = sum(1 for r in resultados if r.passou)
        falhou = sum(1 for r in resultados if not r.passou)

        for r in resultados:
            estilo = self.style.SUCCESS if r.passou else self.style.ERROR
            self.stdout.write(estilo(str(r)))

        self.stdout.write("=" * 65)
        self.stdout.write(f"Total: {len(resultados)}  PASS: {passou}  FAIL: {falhou}")
        self.stdout.write("=" * 65)

        if falhou > 0:
            self.stdout.write(self.style.ERROR("\nDRILL FAIL — corrigir e re-rodar"))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS("\nDRILL PASS — estrutura M6 ok"))
