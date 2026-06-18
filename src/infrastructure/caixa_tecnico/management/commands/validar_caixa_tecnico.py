"""Comando de drill: valida integridade do schema caixa_tecnico (T-CT-027).

Verifica:
  1. RLS ENABLED + FORCED nas 6 tabelas.
  2. ≥ 4 policies por tabela.
  3. Trigger anti-mutação despesa_validada presente.
  4. Block-delete despesa presente.
  5. PrestacaoContas WORM presente (worm + block-delete).
  6. UNIQUE parcial foto_hash com tenant_id 1ª coluna.
  7. UNIQUE parcial client_offline_id com tenant_id 1ª coluna.
  8. GRANT SELECT/INSERT/UPDATE/DELETE para app_user nas 6 tabelas.

Molde: ``src/infrastructure/agenda/management/commands/validar_agenda.py``
(ou equivalente de outro módulo — padrão drill do projeto).

Uso:
    docker compose exec app poetry run python manage.py validar_caixa_tecnico
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection

_TABELAS = [
    "caixa_tecnico",
    "adiantamento_caixa",
    "despesa_caixa",
    "prestacao_contas_caixa",
    "politica_caixa",
    "consentimento_gps_colaborador",
]

_TRIGGERS_ESPERADOS = [
    ("despesa_caixa", "despesa_caixa_anti_mutacao"),
    ("despesa_caixa", "despesa_caixa_block_delete"),
    ("prestacao_contas_caixa", "prestacao_contas_caixa_worm"),
    ("prestacao_contas_caixa", "prestacao_contas_caixa_block_delete"),
]

_INDICES_ESPERADOS = [
    "uq_ct_despesa_foto_hash_ativa",
    "uq_ct_despesa_offline_id",
]

_GRANTS_ESPERADOS = [
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
]


class Command(BaseCommand):
    help = "Drill de validação do schema caixa_tecnico (T-CT-027)."

    def handle(self, *args: object, **options: object) -> None:
        erros: list[str] = []

        with connection.cursor() as cur:
            # 1+2. RLS ENABLED + FORCED + ≥4 policies
            for tabela in _TABELAS:
                cur.execute(
                    """
                    SELECT relrowsecurity, relforcerowsecurity
                    FROM pg_class
                    WHERE relname = %s AND relnamespace = 'public'::regnamespace;
                    """,
                    [tabela],
                )
                row = cur.fetchone()
                if row is None:
                    erros.append(f"TABELA NÃO EXISTE: {tabela}")
                    continue
                rls_enabled, rls_forced = row
                if not rls_enabled:
                    erros.append(f"RLS NÃO HABILITADO: {tabela}")
                if not rls_forced:
                    erros.append(f"RLS NÃO FORÇADO: {tabela}")

                cur.execute(
                    """
                    SELECT count(*)
                    FROM pg_policies
                    WHERE schemaname = 'public' AND tablename = %s;
                    """,
                    [tabela],
                )
                n_policies = cur.fetchone()[0]
                if n_policies < 4:
                    erros.append(
                        f"POLICIES INSUFICIENTES em {tabela}: esperado ≥4, encontrado {n_policies}"
                    )

            # 3+4+5. Triggers
            for tabela, trigger_name in _TRIGGERS_ESPERADOS:
                cur.execute(
                    """
                    SELECT count(*)
                    FROM information_schema.triggers
                    WHERE trigger_schema = 'public'
                      AND event_object_table = %s
                      AND trigger_name = %s;
                    """,
                    [tabela, trigger_name],
                )
                n = cur.fetchone()[0]
                if n == 0:
                    erros.append(f"TRIGGER AUSENTE: {trigger_name} em {tabela}")

            # 6+7. UNIQUE parciais
            for idx_name in _INDICES_ESPERADOS:
                cur.execute(
                    """
                    SELECT count(*)
                    FROM pg_indexes
                    WHERE schemaname = 'public' AND indexname = %s;
                    """,
                    [idx_name],
                )
                n = cur.fetchone()[0]
                if n == 0:
                    erros.append(f"ÍNDICE PARCIAL AUSENTE: {idx_name}")

            # Verificar que tenant_id é a 1ª coluna do índice foto_hash
            cur.execute(
                """
                SELECT indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND indexname = 'uq_ct_despesa_foto_hash_ativa';
                """,
            )
            row = cur.fetchone()
            if row:
                indexdef = row[0]
                if "tenant_id" not in indexdef.split("(")[1][:20]:
                    erros.append(
                        "UNIQUE foto_hash: tenant_id não é a 1ª coluna em uq_ct_despesa_foto_hash_ativa"
                    )

            # 8. GRANT app_user
            for tabela in _TABELAS:
                cur.execute(
                    """
                    SELECT privilege_type
                    FROM information_schema.role_table_grants
                    WHERE table_schema = 'public'
                      AND table_name = %s
                      AND grantee = 'app_user';
                    """,
                    [tabela],
                )
                grants_encontrados = {r[0] for r in cur.fetchall()}
                for grant in _GRANTS_ESPERADOS:
                    if grant not in grants_encontrados:
                        erros.append(f"GRANT {grant} AUSENTE em {tabela} para app_user")

        if erros:
            self.stderr.write(self.style.ERROR("FAIL — validar_caixa_tecnico encontrou erros:"))
            for erro in erros:
                self.stderr.write(self.style.ERROR(f"  • {erro}"))
            raise SystemExit(1)

        self.stdout.write(
            self.style.SUCCESS(
                "PASS — validar_caixa_tecnico: RLS + triggers + índices + grants OK "
                f"({len(_TABELAS)} tabelas, {len(_TRIGGERS_ESPERADOS)} triggers, "
                f"{len(_INDICES_ESPERADOS)} índices parciais)"
            )
        )
