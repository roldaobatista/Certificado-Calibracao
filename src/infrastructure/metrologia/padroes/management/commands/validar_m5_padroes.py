"""T-PAD-072 — drill `validar_m5_padroes` (M5 P8, estrutural).

Verifica que migrations + objetos de seguranca + triggers PG do M5
metrologia/padroes foram aplicados corretamente. Roda no banco apos migrate.

Espelha `validar_m4_calibracao` (mesmo molde DrillResult). Cobre SO o que e
verificavel por introspeccao de catalogo PG (roda sem dados):
  1. 6 tabelas M5 existem
  2. RLS ENABLED nas 6 tabelas (INV-TENANT-001)
  3. RLS FORCE nas 6 tabelas (NOBYPASSRLS — ADR-0002 / INV-TENANT-002)
  4. >=4 policies RLS por tabela (migration 0002 pattern v2)
  5. UNIQUE (tenant_id, numero_serie) em padrao_metrologico (INV-PAD-001)
  6. 6 triggers WORM/incertezas presentes nas tabelas certas (migration 0003)
  7. 3 CHECK jsonb_array_length>0 em padrao_metrologico (INV-PAD-002 / 0006)
  8. app_user tem SELECT/INSERT/UPDATE/DELETE nas 6 tabelas (migration 0004)
  9. GUC app.padrao_recal_em_curso resetado em conexao limpa (C-10)
  10. indices de suporte presentes (migration 0001)

Saida: tabela legivel + exit code 0 (PASS) ou 1 (FAIL).

Uso:
    docker compose exec app poetry run python manage.py validar_m5_padroes

GATE-PAD-DRILL-LOCAL (PG real — FORA deste drill estrutural; coberto pela suite
de regressao contra PostgreSQL real):
  - RLS isolamento cross-tenant (2 tenants intercalados).
  - INV-PAD-006 comportamento do trigger (UPDATE direto RAISE; com GUC passa).
  - INV-SOFT-002 DELETE fisico RAISE; WORM append-only/one-shot (VI/ACC/recal/PT).
    -> tests/regressao/test_inv_pad_p2_schema_triggers.py.
  - INV-PAD-005 perfil A bloqueia RBC; INV-PAD-007 auxiliar vencido bloqueia
    principal; carta Shewhart perfil A -> tests/regressao/test_inv_pad_classes_nomeadas.py.
  - Concorrencia GUC/pool (C-10) sob contencao real de conexoes.
"""

from __future__ import annotations

import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

TABELAS_M5 = [
    "padrao_metrologico",
    "recal_externo_padrao",
    "verificacao_intermediaria",
    "intercomparacao_pt",
    "analise_carta_controle",
    "vinculo_auxiliar",
]

# trigger_name -> tabela esperada (migration 0003_triggers_worm.py)
TRIGGERS_WORM = {
    "padrao_incertezas_so_via_recal_trg": "padrao_metrologico",
    "padrao_block_delete_trg": "padrao_metrologico",
    "recal_externo_padrao_worm_trg": "recal_externo_padrao",
    "verificacao_intermediaria_append_only_trg": "verificacao_intermediaria",
    "intercomparacao_pt_worm_trg": "intercomparacao_pt",
    "analise_carta_controle_append_only_trg": "analise_carta_controle",
}

CHECKS_JSONB = (
    "ck_pad_grandezas_nao_vazio",
    "ck_pad_faixas_nao_vazio",
    "ck_pad_incertezas_certificado_nao_vazio",
)

INDICES_ESPERADOS = ("pad_tenant_est_recal_idx", "pad_tenant_subtipo_idx")

_PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE")


class DrillResult:
    """Resultado de UMA verificacao."""

    def __init__(self, nome: str, passou: bool, detalhe: str = "") -> None:
        self.nome = nome
        self.passou = passou
        self.detalhe = detalhe

    def __str__(self) -> str:
        marca = "PASS" if self.passou else "FAIL"
        return f"  [{marca}] {self.nome}" + (
            f" — {self.detalhe}" if self.detalhe else ""
        )


def _verificar_tabelas_existem() -> list[DrillResult]:
    """Check 1: 6 tabelas M5 existem no banco."""
    with connection.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        existentes = {row[0] for row in cur.fetchall()}
    return [
        DrillResult(
            f"tabela {tab} existe",
            passou=(tab in existentes),
            detalhe="" if tab in existentes else "AUSENTE",
        )
        for tab in TABELAS_M5
    ]


def _verificar_rls() -> list[DrillResult]:
    """Check 2+3: RLS ENABLED + FORCE nas 6 tabelas (INV-TENANT-001/002)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND c.relname = ANY(%s)
            """,
            [TABELAS_M5],
        )
        status = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

    resultados: list[DrillResult] = []
    for tab in TABELAS_M5:
        enabled, force = status.get(tab, (False, False))
        resultados.append(
            DrillResult(
                f"RLS ENABLED em {tab}",
                passou=bool(enabled),
                detalhe="" if enabled else "RLS NAO HABILITADO (INV-TENANT-001)",
            )
        )
        resultados.append(
            DrillResult(
                f"RLS FORCE em {tab}",
                passou=bool(force),
                detalhe="" if force else "FORCE NAO HABILITADO (INV-TENANT-002)",
            )
        )
    return resultados


def _verificar_policies() -> list[DrillResult]:
    """Check 4: >=4 policies RLS por tabela (migration 0002 pattern v2)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT tablename, COUNT(*) FROM pg_policies
            WHERE schemaname = 'public' AND tablename = ANY(%s)
            GROUP BY tablename
            """,
            [TABELAS_M5],
        )
        counts = dict(cur.fetchall())
    return [
        DrillResult(
            f">=4 policies RLS em {tab} (achou {counts.get(tab, 0)})",
            passou=(counts.get(tab, 0) >= 4),
            detalhe="" if counts.get(tab, 0) >= 4 else "policies insuficientes",
        )
        for tab in TABELAS_M5
    ]


def _verificar_unique_numero_serie() -> DrillResult:
    """Check 5: UNIQUE (tenant_id, numero_serie) em padrao_metrologico (INV-PAD-001)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT indexdef FROM pg_indexes
            WHERE tablename = 'padrao_metrologico'
              AND indexdef ILIKE '%UNIQUE%'
              AND indexdef ILIKE '%tenant_id%'
              AND indexdef ILIKE '%numero_serie%'
            """
        )
        ok = cur.fetchone() is not None
    return DrillResult(
        "UNIQUE (tenant_id, numero_serie) padrao_metrologico INV-PAD-001",
        passou=ok,
        detalhe="" if ok else "indice UNIQUE composto AUSENTE",
    )


def _verificar_triggers_worm() -> list[DrillResult]:
    """Check 6: 6 triggers WORM/incertezas presentes nas tabelas certas."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT trigger_name, event_object_table
            FROM information_schema.triggers
            WHERE trigger_name = ANY(%s)
            """,
            [list(TRIGGERS_WORM.keys())],
        )
        encontrados = {row[0]: row[1] for row in cur.fetchall()}

    resultados: list[DrillResult] = []
    for trg, tab_esperada in TRIGGERS_WORM.items():
        tab_real = encontrados.get(trg)
        ok = tab_real == tab_esperada
        resultados.append(
            DrillResult(
                f"trigger {trg} em {tab_esperada}",
                passou=ok,
                detalhe=(
                    ""
                    if ok
                    else f"AUSENTE ou em tabela errada (achou {tab_real!r})"
                ),
            )
        )
    return resultados


def _verificar_check_jsonb() -> list[DrillResult]:
    """Check 7: 3 CHECK jsonb_array_length>0 em padrao_metrologico (0006)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'padrao_metrologico'::regclass
              AND contype = 'c'
              AND conname = ANY(%s)
            """,
            [list(CHECKS_JSONB)],
        )
        existentes = {row[0] for row in cur.fetchall()}
    return [
        DrillResult(
            f"CHECK {c} (INV-PAD-002 / migration 0006)",
            passou=(c in existentes),
            detalhe="" if c in existentes else "AUSENTE",
        )
        for c in CHECKS_JSONB
    ]


def _verificar_grants_app_user() -> list[DrillResult]:
    """Check 8: app_user tem SELECT/INSERT/UPDATE/DELETE nas 6 tabelas.

    Usa has_table_privilege (robusto: cobre grant direto e privilegio implicito
    do OWNER em test, onde OWNER=app_user — memoria feedback_test_db_owner_app_user).
    """
    resultados: list[DrillResult] = []
    with connection.cursor() as cur:
        for tab in TABELAS_M5:
            faltando = []
            for priv in _PRIVILEGIOS:
                cur.execute(
                    "SELECT has_table_privilege('app_user', %s, %s)", [tab, priv]
                )
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


def _verificar_guc_resetado() -> DrillResult:
    """Check 9: GUC app.padrao_recal_em_curso NULL em conexao limpa (C-10)."""
    with connection.cursor() as cur:
        cur.execute("SELECT current_setting('app.padrao_recal_em_curso', true)")
        valor = cur.fetchone()[0]
    ok = valor in (None, "", "0")
    return DrillResult(
        "GUC app.padrao_recal_em_curso resetado em conexao limpa (C-10)",
        passou=ok,
        detalhe="" if ok else f"GUC vazou valor {valor!r} — INV-PAD-006",
    )


def _verificar_indices_suporte() -> list[DrillResult]:
    """Check 10: indices de suporte (migration 0001 AddIndex)."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = ANY(%s)",
            [TABELAS_M5],
        )
        existentes = {row[0] for row in cur.fetchall()}
    return [
        DrillResult(
            f"indice {idx} presente",
            passou=(idx in existentes),
            detalhe="" if idx in existentes else "AUSENTE",
        )
        for idx in INDICES_ESPERADOS
    ]


def rodar_todas_verificacoes() -> list[DrillResult]:
    """Roda todas as categorias estruturais + retorna lista plana."""
    resultados: list[DrillResult] = []
    resultados.extend(_verificar_tabelas_existem())
    resultados.extend(_verificar_rls())
    resultados.extend(_verificar_policies())
    resultados.append(_verificar_unique_numero_serie())
    resultados.extend(_verificar_triggers_worm())
    resultados.extend(_verificar_check_jsonb())
    resultados.extend(_verificar_grants_app_user())
    resultados.append(_verificar_guc_resetado())
    resultados.extend(_verificar_indices_suporte())
    return resultados


class Command(BaseCommand):
    help = "Drill estrutural M5 padroes (T-PAD-072) — verifica migrations/triggers/RLS."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("=" * 65)
        self.stdout.write("Drill validar_m5_padroes — verificacoes estruturais")
        self.stdout.write("=" * 65)

        resultados = rodar_todas_verificacoes()

        passou = sum(1 for r in resultados if r.passou)
        falhou = sum(1 for r in resultados if not r.passou)
        total = len(resultados)

        for r in resultados:
            if r.passou:
                self.stdout.write(self.style.SUCCESS(str(r)))
            else:
                self.stdout.write(self.style.ERROR(str(r)))

        self.stdout.write("=" * 65)
        self.stdout.write(f"Total: {total}  PASS: {passou}  FAIL: {falhou}")
        self.stdout.write("=" * 65)

        if falhou > 0:
            self.stdout.write(self.style.ERROR("\nDRILL FAIL — corrigir e re-rodar"))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS("\nDRILL PASS — estrutura M5 ok"))
