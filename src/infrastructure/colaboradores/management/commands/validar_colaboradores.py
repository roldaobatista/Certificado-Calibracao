"""Drill `validar_colaboradores` (Fatia 1b, estrutural — T-COL-029).

Verifica que migrations + RLS + trigger defensivo + índices/CHECKs + grants +
seed authz + seed catálogo do módulo foram aplicados corretamente.

Checks:
  1. 5 tabelas existem (colaborador, colaborador_papel, colaborador_habilidade,
     colaborador_documento, catalogo_habilidade)
  2. RLS ENABLED + FORCE + >=4 policies nas 4 tabelas-tenant
  3. catalogo_habilidade NÃO tem RLS (relrowsecurity=FALSE — global read-only)
  4. Índices parciais: uq_col_cpf_ativo, uq_col_papel_dono_unico
  5. CHECKs: ck_col_comissao_range, ck_col_hab_xor
  6. Trigger: colaborador_block_delete_trg em colaborador
  7. Grants app_user: SELECT+INSERT+UPDATE+DELETE nas 4 tabelas-tenant;
     SELECT em catalogo_habilidade
  8. Seed authz: 10 ações colaboradores.* presentes
  9. Seed catálogo: >=10 habilidades em catalogo_habilidade

Comportamento PG real (RLS cross-tenant + trigger + índices parciais + CHECKs)
é coberto por tests/test_colaboradores_schema_fatia1b.py.

Uso:
    docker compose exec app poetry run python manage.py validar_colaboradores
"""

from __future__ import annotations

import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

TABELAS_TENANT = (
    "colaborador",
    "colaborador_papel",
    "colaborador_habilidade",
    "colaborador_documento",
)

INDICES_PARCIAIS = (
    "uq_col_cpf_ativo",
    "uq_col_papel_dono_unico",
)

CHECKS = (
    "ck_col_comissao_range",
    "ck_col_hab_xor",
)

TRIGGER = ("colaborador", "colaborador_block_delete_trg")

ACOES_SEED = (
    "colaboradores.cadastrar",
    "colaboradores.editar",
    "colaboradores.desligar",
    "colaboradores.ver",
    "colaboradores.ver_pii",
    "colaboradores.gerir_papel",
    "colaboradores.gerir_habilidade",
    "colaboradores.ver_comissao",
    "colaboradores.ver_auditoria",
    "colaboradores.consultar_elegiveis",
)

GRANTS_FULL = ("colaborador", "colaborador_papel", "colaborador_habilidade", "colaborador_documento")


def _fetchone(cur: Any) -> Any:
    """Wrapper tipado: mypy não infere tipo de cursor.fetchone() (DB-API retorna Sequence).

    Usa assert para garantir não-None (falha ruidosa em contexto de management command).
    Retorno tipado como Any para compatibilidade com DB-API 2.0 (sem stubs precisos).
    """
    row = cur.fetchone()
    assert row is not None, "cursor.fetchone() retornou None inesperadamente"
    return row


class Command(BaseCommand):
    help = "Drill estrutural da frente colaboradores (Fatia 1b)."

    def handle(self, *args: object, **options: object) -> None:
        resultados: list[tuple[bool, str]] = []

        def check(ok: bool, msg: str) -> None:
            resultados.append((ok, msg))
            estilo = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(estilo(f"  [{'PASS' if ok else 'FAIL'}] {msg}"))

        with connection.cursor() as cur:
            # 1. Tabelas existem
            for t in (*TABELAS_TENANT, "catalogo_habilidade"):
                cur.execute("SELECT to_regclass(%s) IS NOT NULL;", [f"public.{t}"])
                check(_fetchone(cur)[0], f"tabela {t} existe")

            # 2. RLS ENABLED + FORCE + >=4 policies nas tabelas-tenant
            for t in TABELAS_TENANT:
                cur.execute(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
                    "JOIN pg_namespace n ON c.relnamespace=n.oid "
                    "WHERE n.nspname='public' AND c.relname=%s;",
                    [t],
                )
                row = cur.fetchone()
                cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s;", [t])
                n_pol = _fetchone(cur)[0]
                check(
                    bool(row and row[0] and row[1] and n_pol >= 4),
                    f"RLS ENABLED+FORCE + {n_pol} policies em {t}",
                )

            # 3. catalogo_habilidade NÃO tem RLS (global read-only)
            cur.execute(
                "SELECT relrowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON c.relnamespace=n.oid "
                "WHERE n.nspname='public' AND c.relname='catalogo_habilidade';",
            )
            row_cat = cur.fetchone()
            check(
                bool(row_cat and not row_cat[0]),
                "catalogo_habilidade sem RLS (global read-only — TL-COL-10)",
            )

            # 4. Índices parciais
            for idx in INDICES_PARCIAIS:
                cur.execute(
                    "SELECT COUNT(*) FROM pg_indexes "
                    "WHERE schemaname='public' AND indexname=%s;",
                    [idx],
                )
                check(_fetchone(cur)[0] >= 1, f"índice parcial {idx} existe")

            # 5. CHECKs
            for ck in CHECKS:
                cur.execute(
                    "SELECT COUNT(*) FROM pg_constraint "
                    "WHERE conname=%s AND contype='c';",
                    [ck],
                )
                check(_fetchone(cur)[0] >= 1, f"CHECK {ck} existe")

            # 6. Trigger defensivo
            tabela_trg, nome_trg = TRIGGER
            cur.execute(
                "SELECT COUNT(*) FROM pg_trigger t "
                "JOIN pg_class c ON t.tgrelid=c.oid "
                "WHERE c.relname=%s AND t.tgname=%s;",
                [tabela_trg, nome_trg],
            )
            check(_fetchone(cur)[0] >= 1, f"trigger {nome_trg} em {tabela_trg}")

            # 7. Grants app_user — SELECT+INSERT+UPDATE+DELETE nas tabelas-tenant
            for t in GRANTS_FULL:
                cur.execute(
                    "SELECT has_table_privilege('app_user', %s, 'SELECT') "
                    "AND has_table_privilege('app_user', %s, 'INSERT') "
                    "AND has_table_privilege('app_user', %s, 'UPDATE') "
                    "AND has_table_privilege('app_user', %s, 'DELETE');",
                    [t, t, t, t],
                )
                check(_fetchone(cur)[0], f"app_user tem SELECT+INSERT+UPDATE+DELETE em {t}")

            # 7b. SELECT em catalogo_habilidade
            cur.execute(
                "SELECT has_table_privilege('app_user', 'catalogo_habilidade', 'SELECT');",
            )
            check(_fetchone(cur)[0], "app_user tem SELECT em catalogo_habilidade")

            # 8. Seed authz — 10 ações colaboradores.*
            cur.execute(
                "SELECT COUNT(DISTINCT acao) FROM authz_perfil_acao "
                "WHERE acao = ANY(%s);",
                [list(ACOES_SEED)],
            )
            n_acoes = _fetchone(cur)[0]
            check(n_acoes == 10, f"seed authz colaboradores: {n_acoes}/10 ações presentes")

            # 9. Seed catálogo — >=10 habilidades
            cur.execute("SELECT COUNT(*) FROM catalogo_habilidade;")
            n_hab = _fetchone(cur)[0]
            check(n_hab >= 10, f"seed catalogo_habilidade: {n_hab} habilidades (mín 10)")

        # Resultado final
        falhas = [msg for ok, msg in resultados if not ok]
        self.stdout.write("")
        if falhas:
            self.stdout.write(
                self.style.ERROR(f"RESULTADO: {len(falhas)} falha(s) em {len(resultados)} checks.")
            )
            sys.exit(1)
        else:
            self.stdout.write(
                self.style.SUCCESS(f"RESULTADO: todos os {len(resultados)} checks PASS.")
            )
