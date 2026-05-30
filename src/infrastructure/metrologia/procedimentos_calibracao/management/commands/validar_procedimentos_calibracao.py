"""T-PROC-027 — drill `validar_procedimentos_calibracao` (M7 Fatia 1b, estrutural).

Verifica que migrations + RLS + triggers WORM + grants do M7 foram aplicados.
Roda no banco após migrate. Espelha `validar_escopos_cmc` (M6). Cobre só o
verificável por introspecção de catálogo PG; o COMPORTAMENTO (triggers/RLS
cross-tenant/UNIQUE parcial) fica em tests/regressao/test_inv_proc_p2_schema_triggers.py
(GATE-PROC-DRILL-LOCAL).

Uso:
    docker compose exec app poetry run python manage.py validar_procedimentos_calibracao
"""

from __future__ import annotations

import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

TABELA = "procedimento_calibracao"

TRIGGERS_WORM = {
    "procedimento_calibracao_block_delete_trg": TABELA,
    "procedimento_calibracao_worm_check_trg": TABELA,
}

INDICE_RESOLUCAO = "proc_resolucao_idx"
INDICES_ESPERADOS = ("proc_resolucao_idx", "proc_tenant_codigo_idx")
UNIQUES = ("uq_proc_chave_documental", "uq_proc_uma_vigente")
_PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE")


class DrillResult:
    def __init__(self, nome: str, passou: bool, detalhe: str = "") -> None:
        self.nome = nome
        self.passou = passou
        self.detalhe = detalhe

    def __str__(self) -> str:
        marca = "PASS" if self.passou else "FAIL"
        return f"  [{marca}] {self.nome}" + (f" — {self.detalhe}" if self.detalhe else "")


def _verificar_tabela() -> DrillResult:
    with connection.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename=%s", [TABELA])
        existe = cur.fetchone() is not None
    return DrillResult(f"tabela {TABELA} existe", passou=existe, detalhe="" if existe else "AUSENTE")


def _verificar_rls() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relkind='r' AND c.relname=%s",
            [TABELA],
        )
        row = cur.fetchone() or (False, False)
        cur.execute(
            "SELECT COUNT(*) FROM pg_policies WHERE schemaname='public' AND tablename=%s",
            [TABELA],
        )
        n_policies = cur.fetchone()[0]
    return [
        DrillResult(f"RLS ENABLED em {TABELA}", passou=bool(row[0]), detalhe="" if row[0] else "INV-TENANT-001"),
        DrillResult(f"RLS FORCE em {TABELA}", passou=bool(row[1]), detalhe="" if row[1] else "INV-TENANT-002"),
        DrillResult(f">=4 policies RLS em {TABELA} (achou {n_policies})", passou=(n_policies >= 4), detalhe="" if n_policies >= 4 else "policies insuficientes"),
    ]


def _verificar_uniques() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute("SELECT indexname FROM pg_indexes WHERE tablename=%s", [TABELA])
        existentes = {r[0] for r in cur.fetchall()}
    return [
        DrillResult(f"UNIQUE {u} presente", passou=(u in existentes), detalhe="" if u in existentes else "AUSENTE")
        for u in UNIQUES
    ]


def _verificar_triggers_worm() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT trigger_name, event_object_table FROM information_schema.triggers "
            "WHERE trigger_name = ANY(%s)",
            [list(TRIGGERS_WORM.keys())],
        )
        encontrados = {r[0]: r[1] for r in cur.fetchall()}
    return [
        DrillResult(
            f"trigger {trg} em {tab}",
            passou=(encontrados.get(trg) == tab),
            detalhe="" if encontrados.get(trg) == tab else f"AUSENTE (achou {encontrados.get(trg)!r})",
        )
        for trg, tab in TRIGGERS_WORM.items()
    ]


def _verificar_indice_parcial() -> DrillResult:
    with connection.cursor() as cur:
        cur.execute("SELECT indexdef FROM pg_indexes WHERE indexname=%s", [INDICE_RESOLUCAO])
        row = cur.fetchone()
    indexdef = (row[0] if row else "") or ""
    ok = "WHERE" in indexdef.upper() and "PUBLICADO" in indexdef and "revogado_em" in indexdef
    return DrillResult(
        f"indice parcial {INDICE_RESOLUCAO} com condicao PUBLICADO",
        passou=ok,
        detalhe="" if ok else f"condicao parcial ausente: {indexdef!r}",
    )


def _verificar_indices_suporte() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute("SELECT indexname FROM pg_indexes WHERE tablename=%s", [TABELA])
        existentes = {r[0] for r in cur.fetchall()}
    return [
        DrillResult(f"indice {idx} presente", passou=(idx in existentes), detalhe="" if idx in existentes else "AUSENTE")
        for idx in INDICES_ESPERADOS
    ]


def _verificar_grants() -> DrillResult:
    faltando = []
    with connection.cursor() as cur:
        for priv in _PRIVILEGIOS:
            cur.execute("SELECT has_table_privilege('app_user', %s, %s)", [TABELA, priv])
            if not cur.fetchone()[0]:
                faltando.append(priv)
    return DrillResult(
        f"app_user tem {'/'.join(_PRIVILEGIOS)} em {TABELA}",
        passou=not faltando,
        detalhe="" if not faltando else f"faltando: {faltando}",
    )


def rodar_todas_verificacoes() -> list[DrillResult]:
    resultados: list[DrillResult] = [_verificar_tabela()]
    resultados.extend(_verificar_rls())
    resultados.extend(_verificar_uniques())
    resultados.extend(_verificar_triggers_worm())
    resultados.append(_verificar_indice_parcial())
    resultados.extend(_verificar_indices_suporte())
    resultados.append(_verificar_grants())
    return resultados


class Command(BaseCommand):
    help = "Drill estrutural M7 procedimentos-calibracao (T-PROC-027)."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("=" * 65)
        self.stdout.write("Drill validar_procedimentos_calibracao — verificacoes estruturais")
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
        self.stdout.write(self.style.SUCCESS("\nDRILL PASS — estrutura M7 ok"))
