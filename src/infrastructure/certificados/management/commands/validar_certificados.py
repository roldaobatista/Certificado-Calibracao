"""T-CER-028 — drill `validar_certificados` (M8 Fatia 1b, estrutural).

Verifica migrations + colunas aditivas + RLS + triggers WORM + grants + sequence +
**trigger INV-025 INTACTO** (contrato cross-app ADR-0078). Roda após migrate; cobre
só o verificável por introspecção de catálogo PG — o COMPORTAMENTO (RLS cross-tenant,
WORM, INV-025 trava equipamento) fica em tests/regressao/test_inv_cer_p2_schema_triggers.py
(GATE-CER-DRILL-LOCAL).

Uso:
    docker compose exec app poetry run python manage.py validar_certificados
"""

from __future__ import annotations

import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

TABELAS_RLS = ("certificados", "ponto_reconciliado", "analise_reconciliacao_cert")
COLUNAS_ADITIVAS_CERT = (
    "calibracao_id",
    "numero_interno",
    "numero_certificado",
    "versao",
    "versao_anterior_id",
    "perfil_emissor_no_momento",
    "faixa_certificado_min",
    "faixa_certificado_max",
    "tipo_acreditacao",
    "snapshot_equipamento_json",
    "snapshot_padroes_usados_json",
    "regra_decisao_snapshot",
    "reconciliacao_hash",
    "correlation_id",
    "revision",
)
TRIGGERS_WORM = {
    "ponto_reconciliado_block_delete_trg": "ponto_reconciliado",
    "ponto_reconciliado_worm_check_trg": "ponto_reconciliado",
    "analise_reconciliacao_cert_block_delete_trg": "analise_reconciliacao_cert",
    "analise_reconciliacao_cert_worm_check_trg": "analise_reconciliacao_cert",
    "certificado_emissao_worm_check_trg": "certificados",
}
UNIQUES = {
    "certificados": ("uq_cert_calibracao_versao",),
    "ponto_reconciliado": ("uq_ponto_recon_cert_ponto",),
    "analise_reconciliacao_cert": ("uq_analise_recon_calibracao_ponto",),
}
TABELAS_GRANT = ("ponto_reconciliado", "analise_reconciliacao_cert")
_PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE")
INV_025_TRIGGER = "equipamento_imutabilidade_pos_cert_trg"
INV_025_FUNC = "equipamento_imutabilidade_pos_cert_check"


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
            cur.execute("SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename=%s", [t])
            existe = cur.fetchone() is not None
            out.append(DrillResult(f"tabela {t} existe", passou=existe, detalhe="" if existe else "AUSENTE"))
    return out


def _verificar_colunas_aditivas() -> list[DrillResult]:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='certificados'"
        )
        existentes = {r[0] for r in cur.fetchall()}
    return [
        DrillResult(f"coluna certificados.{c}", passou=(c in existentes), detalhe="" if c in existentes else "AUSENTE")
        for c in COLUNAS_ADITIVAS_CERT
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
            cur.execute("SELECT COUNT(*) FROM pg_policies WHERE schemaname='public' AND tablename=%s", [t])
            n = cur.fetchone()[0]
            out.append(DrillResult(f"RLS ENABLE+FORCE+>=4 policies em {t} (achou {n})", passou=bool(row[0]) and bool(row[1]) and n >= 4, detalhe="" if (row[0] and row[1] and n >= 4) else "INV-TENANT-001/002/003"))
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
        DrillResult(f"trigger {trg} em {tab}", passou=(encontrados.get(trg) == tab), detalhe="" if encontrados.get(trg) == tab else f"AUSENTE (achou {encontrados.get(trg)!r})")
        for trg, tab in TRIGGERS_WORM.items()
    ]


def _verificar_inv_025_intacto() -> list[DrillResult]:
    """ADR-0078: a migration aditiva NÃO pode quebrar o contrato cross-app."""
    out = []
    with connection.cursor() as cur:
        cur.execute(
            "SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_name=%s",
            [INV_025_TRIGGER],
        )
        row = cur.fetchone()
        out.append(DrillResult(f"trigger INV-025 {INV_025_TRIGGER} em equipamentos", passou=(row is not None and row[1] == "equipamentos"), detalhe="" if (row and row[1] == "equipamentos") else "AUSENTE/MOVIDO"))
        cur.execute("SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname=%s", [INV_025_FUNC])
        frow = cur.fetchone()
        fdef = (frow[0] if frow else "") or ""
        le_emitido = "'emitido'" in fdef and "FROM certificados" in fdef
        out.append(DrillResult("INV-025 ainda le status='emitido' FROM certificados", passou=le_emitido, detalhe="" if le_emitido else "CONTRATO QUEBRADO (ADR-0078)"))
    return out


def _verificar_uniques() -> list[DrillResult]:
    out = []
    with connection.cursor() as cur:
        for tabela, nomes in UNIQUES.items():
            cur.execute("SELECT indexname FROM pg_indexes WHERE tablename=%s", [tabela])
            existentes = {r[0] for r in cur.fetchall()}
            for u in nomes:
                out.append(DrillResult(f"UNIQUE {u} em {tabela}", passou=(u in existentes), detalhe="" if u in existentes else "AUSENTE"))
    return out


def _verificar_grants() -> list[DrillResult]:
    out = []
    with connection.cursor() as cur:
        for t in TABELAS_GRANT:
            faltando = []
            for priv in _PRIVILEGIOS:
                cur.execute("SELECT has_table_privilege('app_user', %s, %s)", [t, priv])
                if not cur.fetchone()[0]:
                    faltando.append(priv)
            out.append(DrillResult(f"app_user tem {'/'.join(_PRIVILEGIOS)} em {t}", passou=not faltando, detalhe="" if not faltando else f"faltando: {faltando}"))
    return out


def _verificar_sequence() -> DrillResult:
    with connection.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_class WHERE relkind='S' AND relname='certificado_numero_seq'")
        existe = cur.fetchone() is not None
    return DrillResult("sequence certificado_numero_seq existe", passou=existe, detalhe="" if existe else "AUSENTE")


def rodar_todas_verificacoes() -> list[DrillResult]:
    resultados: list[DrillResult] = []
    resultados.extend(_verificar_tabelas())
    resultados.extend(_verificar_colunas_aditivas())
    resultados.extend(_verificar_rls())
    resultados.extend(_verificar_triggers_worm())
    resultados.extend(_verificar_inv_025_intacto())
    resultados.extend(_verificar_uniques())
    resultados.extend(_verificar_grants())
    resultados.append(_verificar_sequence())
    return resultados


class Command(BaseCommand):
    help = "Drill estrutural M8 certificados (T-CER-028 / GATE-CER-DRILL-LOCAL)."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("=" * 65)
        self.stdout.write("Drill validar_certificados — verificacoes estruturais (M8)")
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
        self.stdout.write(self.style.SUCCESS("\nDRILL PASS — estrutura M8 certificados ok"))
