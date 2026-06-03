"""T-LIC-022 — drill `validar_licencas_acreditacoes` (M9 Fatia 1b, estrutural).

Verifica as 5 tabelas + colunas da raiz + RLS v2 (ENABLE+FORCE+>=4 policies) +
triggers WORM Padrão B (revisao/evento append-only + raiz block-delete + worm-check) +
grants app_user + UNIQUE idempotência alertas + chave natural. Roda após migrate;
cobre só o verificável por introspecção de catálogo PG — o COMPORTAMENTO (RLS
cross-tenant, WORM) fica em tests/regressao/test_inv_lic_p2_schema_triggers.py.

Uso:
    docker compose exec app poetry run python manage.py validar_licencas_acreditacoes
"""

from __future__ import annotations

import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

TABELAS_RLS = (
    "documento_regulatorio",
    "revisao_documento",
    "alerta_vencimento",
    "bloqueio_operacional",
    "evento_emergencial_licenca",
)
COLUNAS_RAIZ = (
    "tipo",
    "numero",
    "orgao_emissor",
    "vigencia_inicio",
    "vigencia_fim",
    "bloqueante",
    "status_cache",
    "escopo",
    "numero_cgcre",
    "ilac_mra_aderido",
    "titular_referencia_hash",
    "titular_referencia_key_id",
    "responsavel_id",
    "perfil_emissor_no_momento",
    "correlation_id",
    "revision",
    "revogado_em",
    "motivo_revogacao",
)
TRIGGERS_WORM = {
    "revisao_documento_block_update_trg": "revisao_documento",
    "revisao_documento_block_delete_trg": "revisao_documento",
    "evento_emergencial_licenca_block_update_trg": "evento_emergencial_licenca",
    "evento_emergencial_licenca_block_delete_trg": "evento_emergencial_licenca",
    "documento_regulatorio_block_delete_trg": "documento_regulatorio",
    "documento_regulatorio_worm_check_trg": "documento_regulatorio",
}
UNIQUES = {
    "documento_regulatorio": ("uq_documento_regulatorio_chave_natural",),
    "revisao_documento": ("uq_revisao_documento_numero",),
    "alerta_vencimento": ("uq_alerta_vencimento_idempotente",),
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


def _verificar_colunas_raiz() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='documento_regulatorio'"
        )
        existentes = {r[0] for r in cur.fetchall()}
    return [
        DrillResult(
            f"coluna documento_regulatorio.{c}",
            passou=(c in existentes),
            detalhe="" if c in existentes else "AUSENTE",
        )
        for c in COLUNAS_RAIZ
    ]


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


def _verificar_uniques() -> list[DrillResult]:
    out = []
    with connection.cursor() as cur:
        for tabela, nomes in UNIQUES.items():
            cur.execute("SELECT indexname FROM pg_indexes WHERE tablename=%s", [tabela])
            existentes = {r[0] for r in cur.fetchall()}
            for u in nomes:
                out.append(
                    DrillResult(
                        f"UNIQUE {u} em {tabela}",
                        passou=(u in existentes),
                        detalhe="" if u in existentes else "AUSENTE",
                    )
                )
    return out


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
    resultados.extend(_verificar_colunas_raiz())
    resultados.extend(_verificar_rls())
    resultados.extend(_verificar_triggers_worm())
    resultados.extend(_verificar_uniques())
    resultados.extend(_verificar_grants())
    return resultados


class Command(BaseCommand):
    help = "Drill estrutural M9 licencas-acreditacoes (T-LIC-022 / GATE-ECMC-DRILL-LOCAL)."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("=" * 65)
        self.stdout.write("Drill validar_licencas_acreditacoes — estrutural (M9)")
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
        self.stdout.write(self.style.SUCCESS("\nDRILL PASS — estrutura M9 licencas ok"))
