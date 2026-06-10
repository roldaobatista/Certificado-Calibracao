"""Drill `validar_configuracoes_sistema` (Fatia 1b, estrutural — T-CFG-027).

Verifica que migrations + RLS + triggers + exclusion constraint + grants + seed
authz do módulo foram aplicados. Roda após migrate. Espelha o molde
`validar_fiscal_nfse` (DrillResult). Cobre o verificável por introspecção PG:
  1. 5 tabelas existem
  2. RLS ENABLED + FORCE + >=4 policies em cada (INV-TENANT-001/002)
  3. UNIQUEs de negócio (INV-036/037; chave de série TL-06; reserva gap-less)
  4. exclusion constraint btree_gist (INV-CFG-IMPOSTO-SEM-SOBREPOSICAO)
  5. 6 triggers (INV-028 + imposto block-delete/worm + 3 da numeração)
  6. app_user tem SELECT/INSERT/UPDATE/DELETE nas 5 tabelas
  7. seed authz `configuracoes_sistema.*` presente (7 ações)

O comportamento PG real (RLS cross-tenant + triggers + exclusion) é coberto por
tests/test_configuracoes_schema_fatia1b.py.

Uso:
    docker compose exec app poetry run python manage.py validar_configuracoes_sistema
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand
from django.db import connection

TABELAS = (
    "empresa",
    "filial",
    "imposto",
    "serie_documento",
    "numero_documento_reservado",
)

UNIQUES = (
    "uq_cfg_empresa_cnpj",
    "uq_cfg_filial_cnpj",
    "uq_cfg_filial_uma_matriz",
    "uq_cfg_serie_chave_filial",
    "uq_cfg_serie_chave_global",
    "uq_num_doc_reservado",
)

EXCLUSION = "excl_imposto_vigencia_sobreposta"

TRIGGERS = (
    ("serie_documento", "serie_documento_inv028_check_trg"),
    ("imposto", "imposto_block_delete_trg"),
    ("imposto", "imposto_worm_check_trg"),
    ("numero_documento_reservado", "numero_doc_reservado_consecutivo_check_trg"),
    ("numero_documento_reservado", "numero_doc_reservado_confirma_one_shot_trg"),
    ("numero_documento_reservado", "numero_doc_reservado_block_delete_confirmado_trg"),
)

_PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE")

_N_ACOES_AUTHZ = 7


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
        for tabela in TABELAS:
            # 1. tabela existe
            cur.execute(
                "SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename=%s",
                [tabela],
            )
            existe = cur.fetchone() is not None
            res.append(DrillResult(f"tabela {tabela} existe", existe, "" if existe else "AUSENTE"))
            if not existe:
                continue

            # 2. RLS enabled + forced + >=4 policies
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
            cur.execute("SELECT count(*) FROM pg_policies WHERE tablename=%s", [tabela])
            n_pol = cur.fetchone()[0]
            res.append(
                DrillResult(f">=4 policies RLS em {tabela}", n_pol >= 4, f"{n_pol} policies")
            )

            # 6. grants app_user
            cur.execute(
                "SELECT privilege_type FROM information_schema.role_table_grants "
                "WHERE table_name=%s AND grantee='app_user'",
                [tabela],
            )
            privs = {r[0] for r in cur.fetchall()}
            faltam = [p for p in _PRIVILEGIOS if p not in privs]
            res.append(
                DrillResult(
                    f"app_user S/I/U/D em {tabela}",
                    not faltam,
                    f"faltam {faltam}" if faltam else "",
                )
            )

        # 3. UNIQUEs de negócio
        for uq in UNIQUES:
            cur.execute(
                "SELECT 1 FROM pg_constraint WHERE conname=%s AND contype='u' "
                "UNION SELECT 1 FROM pg_indexes WHERE indexname=%s",
                [uq, uq],
            )
            res.append(DrillResult(f"UNIQUE {uq}", cur.fetchone() is not None))

        # 4. exclusion constraint (contype='x')
        cur.execute("SELECT 1 FROM pg_constraint WHERE conname=%s AND contype='x'", [EXCLUSION])
        res.append(
            DrillResult(
                f"EXCLUDE {EXCLUSION} (INV-CFG-IMPOSTO-SEM-SOBREPOSICAO)",
                cur.fetchone() is not None,
            )
        )

        # 5. triggers
        for tabela, trg in TRIGGERS:
            cur.execute(
                "SELECT 1 FROM pg_trigger WHERE tgrelid=%s::regclass AND tgname=%s "
                "AND NOT tgisinternal",
                [tabela, trg],
            )
            res.append(DrillResult(f"trigger {trg}", cur.fetchone() is not None))

        # 7. seed authz
        cur.execute(
            "SELECT count(DISTINCT acao) FROM authz_perfil_acao "
            "WHERE acao LIKE 'configuracoes_sistema.%%'"
        )
        n_acoes = cur.fetchone()[0]
        res.append(
            DrillResult(
                f"seed authz configuracoes_sistema.* ({_N_ACOES_AUTHZ} ações)",
                n_acoes == _N_ACOES_AUTHZ,
                f"{n_acoes} ações",
            )
        )
    return res


class Command(BaseCommand):
    help = "Drill estrutural do módulo configuracoes-sistema (Fatia 1b)."

    def handle(self, *args: object, **options: object) -> None:
        resultados = _verificar()
        self.stdout.write("== validar_configuracoes_sistema ==")
        for r in resultados:
            self.stdout.write(str(r))
        falhas = [r for r in resultados if not r.passou]
        total = len(resultados)
        ok = total - len(falhas)
        self.stdout.write(f"\n{ok}/{total} checks PASS")
        if falhas:
            sys.exit(1)
