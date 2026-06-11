"""Drill `validar_produtos_pecas_servicos` (Fatia 1b, estrutural — T-PPS-023).

Verifica que migrations + RLS + triggers + exclusions + grants + seed authz do
módulo foram aplicados. Espelha o molde `validar_configuracoes_sistema`. Cobre
o verificável por introspecção PG:
  1. 5 tabelas existem
  2. RLS ENABLED + FORCE + >=4 policies em cada (INV-TENANT-001/002)
  3. UNIQUEs de negócio (INV-PPS-CODIGO-UNICO; versao_n; eh_padrao parcial; kit)
  4. CHECKs preco>0 ×2 + quantidade>0 (TL-PPS-16)
  5. 2 exclusion constraints btree_gist (não-sobreposição WHERE revogado IS NULL)
  6. 4 triggers WORM (versão/linha worm + block delete)
  7. app_user tem SELECT/INSERT/UPDATE/DELETE nas 5 tabelas
  8. seed authz `catalogo.*` presente (4 ações)

Comportamento PG real (RLS cross-tenant + triggers + exclusions) é coberto por
tests/test_pps_schema_fatia1b.py.

Uso:
    docker compose exec app poetry run python manage.py validar_produtos_pecas_servicos
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand
from django.db import connection

TABELAS = (
    "item_catalogo",
    "item_catalogo_versao",
    "kit_composicao",
    "tabela_preco",
    "linha_tabela_preco",
)

UNIQUES = (
    "uq_pps_item_codigo",
    "uq_pps_versao_n",
    "uq_pps_kit_filho",
    "uq_pps_tabela_padrao",
)

CHECKS = (
    "ck_pps_versao_preco_positivo",
    "ck_pps_linha_preco_positivo",
    "ck_pps_kit_qtd_positiva",
)

EXCLUSIONS = (
    "excl_pps_versao_vigencia",
    "excl_pps_linha_vigencia",
)

TRIGGERS = (
    ("item_catalogo_versao", "item_catalogo_versao_worm_trg"),
    ("item_catalogo_versao", "item_catalogo_versao_block_delete_trg"),
    ("linha_tabela_preco", "linha_tabela_preco_worm_trg"),
    ("linha_tabela_preco", "linha_tabela_preco_block_delete_trg"),
)

ACOES_SEED = (
    "catalogo.ver",
    "catalogo.editar",
    "catalogo.gerenciar_tabela",
    "catalogo.importar",
)


class Command(BaseCommand):
    help = "Drill estrutural da frente produtos-pecas-servicos (Fatia 1b)."

    def handle(self, *args: object, **options: object) -> None:
        resultados: list[tuple[bool, str]] = []

        def check(ok: bool, msg: str) -> None:
            resultados.append((ok, msg))
            estilo = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(estilo(f"  [{'PASS' if ok else 'FAIL'}] {msg}"))

        with connection.cursor() as cur:
            # 1. tabelas
            for t in TABELAS:
                cur.execute("SELECT to_regclass(%s) IS NOT NULL;", [f"public.{t}"])
                check(cur.fetchone()[0], f"tabela {t} existe")

            # 2. RLS + FORCE + >=4 policies
            for t in TABELAS:
                cur.execute(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
                    "JOIN pg_namespace n ON c.relnamespace=n.oid "
                    "WHERE n.nspname='public' AND c.relname=%s;",
                    [t],
                )
                row = cur.fetchone()
                cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s;", [t])
                n_pol = cur.fetchone()[0]
                check(
                    bool(row and row[0] and row[1] and n_pol >= 4),
                    f"RLS ENABLED+FORCE + {n_pol} policies em {t}",
                )

            # 3/4/5. constraints (UNIQUE parcial vira índice único — checa ambos,
            # molde validar_configuracoes_sistema)
            for nome in UNIQUES + CHECKS + EXCLUSIONS:
                cur.execute(
                    "SELECT 1 FROM pg_constraint WHERE conname=%s "
                    "UNION SELECT 1 FROM pg_indexes WHERE indexname=%s;",
                    [nome, nome],
                )
                check(cur.fetchone() is not None, f"constraint {nome}")

            # 6. triggers
            for tabela, trg in TRIGGERS:
                cur.execute(
                    "SELECT COUNT(*) FROM pg_trigger t JOIN pg_class c ON t.tgrelid=c.oid "
                    "WHERE c.relname=%s AND t.tgname=%s AND NOT t.tgisinternal;",
                    [tabela, trg],
                )
                check(cur.fetchone()[0] == 1, f"trigger {trg} em {tabela}")

            # 7. grants app_user
            for t in TABELAS:
                cur.execute(
                    "SELECT COUNT(*) FROM information_schema.role_table_grants "
                    "WHERE grantee='app_user' AND table_name=%s "
                    "AND privilege_type IN ('SELECT','INSERT','UPDATE','DELETE');",
                    [t],
                )
                check(cur.fetchone()[0] == 4, f"grants app_user em {t}")

            # 8. seed authz
            cur.execute(
                "SELECT COUNT(DISTINCT acao) FROM authz_perfil_acao WHERE acao = ANY(%s);",
                [list(ACOES_SEED)],
            )
            n_acoes = cur.fetchone()[0]
            check(
                n_acoes == len(ACOES_SEED),
                f"seed authz catalogo.* ({n_acoes}/{len(ACOES_SEED)} ações)",
            )

        total = len(resultados)
        ok = sum(1 for r, _ in resultados if r)
        self.stdout.write("")
        if ok == total:
            self.stdout.write(self.style.SUCCESS(f"{ok}/{total} checks PASS"))
        else:
            self.stdout.write(self.style.ERROR(f"{ok}/{total} checks PASS — FALHOU"))
            sys.exit(1)
