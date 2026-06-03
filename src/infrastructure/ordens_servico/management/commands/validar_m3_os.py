"""Drill `validar_m3_os` — M3 `ordens_servico`, estrutural (GATE-OS-VALIDAR-DRILL).

Verifica as 11 tabelas do módulo + colunas-chave (incl. `atividade_da_os.grandeza`
ADR-0063 + `evento_de_os` hash-chain WORM) + RLS v2 (ENABLE+FORCE+≥4 policies) +
6 triggers WORM/anti-mutation + grants `app_user`. Roda após migrate; cobre só o
verificável por introspecção de catálogo PG — o COMPORTAMENTO (RLS cross-tenant, WORM)
fica nos testes de regressão M3 (`test_inv_os_*`). Molde dos drills metrologia (M4-M9).

Uso:
    docker compose exec app poetry run python manage.py validar_m3_os
"""

from __future__ import annotations

import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

TABELAS_RLS = (
    "ordens_servico",
    "atividade_da_os",
    "tipo_atividade_config",
    "consentimento_biometria_touch",
    "aceite_atividade",
    "evidencia_foto_atividade",
    "evento_de_os",
    "dispensa_aceite_atividade",
    "checklist_da_atividade",
    "nao_conformidade_atividade",
    "sla_contrato",
)

# Colunas-chave por tabela (esqueleto do agregado OS com Atividades — ADR-0023/0063).
COLUNAS_CHAVE = {
    "ordens_servico": (
        "numero_os",
        "estado",
        "tipo_predominante",
        "regra_decisao_acordada",
        "tenant_id",
    ),
    "atividade_da_os": (
        "tipo",
        "estado",
        "grandeza",  # ADR-0063 — predicate rt_competencia_cobre consulta este campo
        "tipo_bloqueia_concorrencia",
        "tenant_id",
    ),
    "evento_de_os": (
        "payload_hash",  # hash-chain WORM (INV-OS-AUD-001)
        "payload_data",
        "correlation_id",
        "perfil_no_evento",  # SAN-PERFIL Sprint 4
        "tenant_id",
    ),
}

# Triggers WORM/anti-mutation reais (introspecção 2026-06-03).
TRIGGERS_WORM = {
    "evento_de_os_append_only_trg": "evento_de_os",
    "evidencia_foto_atividade_append_only_trg": "evidencia_foto_atividade",
    "aceite_atividade_anti_mutation_trg": "aceite_atividade",
    "consentimento_biometria_touch_anti_mutation_trg": "consentimento_biometria_touch",
    "dispensa_aceite_atividade_anti_mutation_trg": "dispensa_aceite_atividade",
    "nao_conformidade_atividade_anti_mutation_trg": "nao_conformidade_atividade",
}
_PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE")


class DrillResult:
    def __init__(self, nome: str, passou: bool, detalhe: str = "") -> None:
        self.nome = nome
        self.passou = passou
        self.detalhe = detalhe

    def __str__(self) -> str:
        marca = "PASS" if self.passou else "FAIL"
        return f"  [{marca}] {self.nome}" + (f" — {self.detalhe}" if self.detalhe else "")


def _verificar_tabelas() -> list[DrillResult]:
    out = []
    with connection.cursor() as cur:
        for t in TABELAS_RLS:
            cur.execute(
                "SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename=%s", [t]
            )
            existe = cur.fetchone() is not None
            out.append(
                DrillResult(f"tabela {t} existe", passou=existe, detalhe="" if existe else "AUSENTE")
            )
    return out


def _verificar_colunas_chave() -> list[DrillResult]:
    out = []
    with connection.cursor() as cur:
        for tabela, colunas in COLUNAS_CHAVE.items():
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s",
                [tabela],
            )
            existentes = {r[0] for r in cur.fetchall()}
            for c in colunas:
                out.append(
                    DrillResult(
                        f"coluna {tabela}.{c}",
                        passou=(c in existentes),
                        detalhe="" if c in existentes else "AUSENTE",
                    )
                )
    return out


def _verificar_rls() -> list[DrillResult]:
    out = []
    with connection.cursor() as cur:
        for t in TABELAS_RLS:
            cur.execute(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='public' AND c.relkind='r' AND c.relname=%s",
                [t],
            )
            row = cur.fetchone() or (False, False)
            cur.execute(
                "SELECT COUNT(*) FROM pg_policies WHERE schemaname='public' AND tablename=%s",
                [t],
            )
            n = cur.fetchone()[0]
            ok = bool(row[0]) and bool(row[1]) and n >= 4
            out.append(
                DrillResult(
                    f"RLS ENABLE+FORCE+>=4 policies em {t} (achou {n})",
                    passou=ok,
                    detalhe="" if ok else "INV-TENANT-001/002/003",
                )
            )
    return out


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


def _verificar_grants() -> list[DrillResult]:
    out = []
    with connection.cursor() as cur:
        for t in TABELAS_RLS:
            faltando = []
            for priv in _PRIVILEGIOS:
                cur.execute("SELECT has_table_privilege('app_user', %s, %s)", [t, priv])
                if not cur.fetchone()[0]:
                    faltando.append(priv)
            out.append(
                DrillResult(
                    f"app_user tem {'/'.join(_PRIVILEGIOS)} em {t}",
                    passou=not faltando,
                    detalhe="" if not faltando else f"faltando: {faltando}",
                )
            )
    return out


def rodar_todas_verificacoes() -> list[DrillResult]:
    resultados: list[DrillResult] = []
    resultados.extend(_verificar_tabelas())
    resultados.extend(_verificar_colunas_chave())
    resultados.extend(_verificar_rls())
    resultados.extend(_verificar_triggers_worm())
    resultados.extend(_verificar_grants())
    return resultados


class Command(BaseCommand):
    help = "Drill estrutural M3 ordens_servico (GATE-OS-VALIDAR-DRILL)."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("=" * 65)
        self.stdout.write("Drill validar_m3_os — estrutural (M3 ordens_servico)")
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
        self.stdout.write(self.style.SUCCESS("\nDRILL PASS — estrutura M3 OS ok"))
