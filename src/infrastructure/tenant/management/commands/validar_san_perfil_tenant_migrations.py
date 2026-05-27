"""Drill estrutural do saneamento SAN-PERFIL-TENANT (Sprint 1).

T-SAN-PERFIL-014 — AC-SAN-PERFIL-001-7.

Valida que as migrations 0003..0009 estao todas aplicadas + objetos no banco
(coluna, CHECK constraints, tabela historico, triggers anti-mutacao, funcoes
SECURITY DEFINER). NAO testa idempotencia em ambiente zerado vs ambiente
ja-M4 (esse e o GATE-TENANT-PERFIL-DRILL-PG-REAL Wave A — exige container
PG real fresco vs container PG ja-rodado).

Uso:
    python manage.py validar_san_perfil_tenant_migrations

Retorna:
- exit 0: todos os 18 checks PASS.
- exit 1: 1+ check FAIL — imprime detalhes.

Cada check imprime [PASS] ou [FAIL] com descricao curta.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection


CHECKS_ESPERADOS = [
    # Cada check = (nome_curto, sql, validador, descricao)
    (
        "schema-coluna-perfil",
        "SELECT column_name, is_nullable, data_type FROM information_schema.columns "
        "WHERE table_name='tenants' AND column_name='perfil_regulatorio'",
        lambda rows: len(rows) == 1 and rows[0][1] == "NO",
        "Coluna tenants.perfil_regulatorio existe + NOT NULL pos-migration 0005",
    ),
    (
        "schema-check-perfil-validos",
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name='tenants' AND constraint_name='tenants_perfil_regulatorio_check'",
        lambda rows: len(rows) == 1,
        "CHECK constraint tenants_perfil_regulatorio_check (A/B/C/D)",
    ),
    (
        "schema-acreditacao-cgcre-numero",
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='tenants' AND column_name='acreditacao_cgcre_numero'",
        lambda rows: len(rows) == 1,
        "Coluna tenants.acreditacao_cgcre_numero (migration 0006)",
    ),
    (
        "schema-acreditacao-suspensa-em",
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='tenants' AND column_name='acreditacao_suspensa_em'",
        lambda rows: len(rows) == 1,
        "Coluna tenants.acreditacao_suspensa_em (NIT-DICLA-005 §7.4)",
    ),
    (
        "schema-acreditacao-suspensa-ate",
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='tenants' AND column_name='acreditacao_suspensa_ate'",
        lambda rows: len(rows) == 1,
        "Coluna tenants.acreditacao_suspensa_ate",
    ),
    (
        "schema-ilac-mra-aderido",
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='tenants' AND column_name='ilac_mra_aderido'",
        lambda rows: len(rows) == 1,
        "Coluna tenants.ilac_mra_aderido (R9 plan.md)",
    ),
    (
        "schema-check-acreditacao-numero-so-A",
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name='tenants' AND constraint_name='tenants_acreditacao_numero_so_perfil_a_check'",
        lambda rows: len(rows) == 1,
        "CHECK constraint acreditacao_numero so quando perfil='A'",
    ),
    (
        "schema-check-ilac-mra-so-A",
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name='tenants' AND constraint_name='tenants_ilac_mra_so_perfil_a_check'",
        lambda rows: len(rows) == 1,
        "CHECK constraint ilac_mra_aderido so quando perfil='A'",
    ),
    (
        "tabela-tenant-perfil-historico",
        "SELECT table_name FROM information_schema.tables WHERE table_name='tenant_perfil_historico'",
        lambda rows: len(rows) == 1,
        "Tabela tenant_perfil_historico (migration 0007)",
    ),
    (
        "check-motivo-minimo-100",
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name='tenant_perfil_historico' AND constraint_name='tph_motivo_minimo_100_chars_check'",
        lambda rows: len(rows) == 1,
        "CHECK constraint motivo >= 100 chars",
    ),
    (
        "check-a3-obrigatoria-em-promocao",
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name='tenant_perfil_historico' AND constraint_name='tph_a3_obrigatoria_em_promocao_check'",
        lambda rows: len(rows) == 1,
        "CHECK constraint A3 obrigatoria em promocao_regulatoria",
    ),
    (
        "trigger-anti-update-historico",
        "SELECT trigger_name FROM information_schema.triggers "
        "WHERE event_object_table='tenant_perfil_historico' AND trigger_name='tph_anti_update_trigger'",
        lambda rows: len(rows) == 1,
        "Trigger anti-UPDATE no historico (append-only)",
    ),
    (
        "trigger-anti-delete-historico",
        "SELECT trigger_name FROM information_schema.triggers "
        "WHERE event_object_table='tenant_perfil_historico' AND trigger_name='tph_anti_delete_trigger'",
        lambda rows: len(rows) == 1,
        "Trigger anti-DELETE no historico (append-only)",
    ),
    (
        "funcao-aplicar-evento-cgcre",
        "SELECT proname FROM pg_proc WHERE proname='aplicar_evento_cgcre'",
        lambda rows: len(rows) == 1,
        "Funcao SECURITY DEFINER aplicar_evento_cgcre (migration 0008)",
    ),
    (
        "funcao-rebaixar-voluntario",
        "SELECT proname FROM pg_proc WHERE proname='rebaixar_perfil_tenant_voluntario_cliente'",
        lambda rows: len(rows) == 1,
        "Funcao SECURITY DEFINER rebaixar_perfil_tenant_voluntario_cliente (migration 0009)",
    ),
    (
        "funcao-aplicar-e-security-definer",
        "SELECT prosecdef FROM pg_proc WHERE proname='aplicar_evento_cgcre'",
        lambda rows: len(rows) == 1 and rows[0][0] is True,
        "aplicar_evento_cgcre tem SECURITY DEFINER (prosecdef=true)",
    ),
    (
        "funcao-rebaixar-e-security-definer",
        "SELECT prosecdef FROM pg_proc WHERE proname='rebaixar_perfil_tenant_voluntario_cliente'",
        lambda rows: len(rows) == 1 and rows[0][0] is True,
        "rebaixar_voluntario tem SECURITY DEFINER (prosecdef=true)",
    ),
    (
        "backfill-balancas-solution-perfil-B",
        "SELECT t.perfil_regulatorio, h.direcao "
        "FROM tenants t LEFT JOIN tenant_perfil_historico h ON h.tenant_id=t.id "
        "WHERE t.slug='balancas-solution' AND h.direcao='provisionamento_inicial'",
        lambda rows: (
            len(rows) >= 1
            and rows[0][0] == "B"
            and rows[0][1] == "provisionamento_inicial"
        ),
        "Balancas Solution = perfil B + historico PROVISIONAMENTO_INICIAL (justificado)",
    ),
]


class Command(BaseCommand):
    help = (
        "Drill estrutural SAN-PERFIL-TENANT — valida schema + funcoes SECURITY DEFINER "
        "+ triggers anti-mutacao + backfill Balancas Solution (T-SAN-PERFIL-014)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fail-fast",
            action="store_true",
            help="Para no primeiro FAIL em vez de listar todos.",
        )
        parser.add_argument(
            "--skip-balancas",
            action="store_true",
            help="Pula check de Balancas Solution (util em ambiente CI sem seed).",
        )

    def handle(self, *args, **options):
        fail_fast = options["fail_fast"]
        skip_balancas = options["skip_balancas"]

        pass_count = 0
        fail_count = 0
        falhas: list[tuple[str, str]] = []

        with connection.cursor() as cur:
            for nome, sql, validador, descricao in CHECKS_ESPERADOS:
                if skip_balancas and nome == "backfill-balancas-solution-perfil-B":
                    self.stdout.write(self.style.WARNING(f"  [SKIP] {nome} (--skip-balancas)"))
                    continue
                try:
                    cur.execute(sql)
                    rows = cur.fetchall()
                    if validador(rows):
                        pass_count += 1
                        self.stdout.write(self.style.SUCCESS(f"  [PASS] {nome} — {descricao}"))
                    else:
                        fail_count += 1
                        falhas.append((nome, descricao))
                        self.stdout.write(
                            self.style.ERROR(f"  [FAIL] {nome} — {descricao} (rows={rows!r})")
                        )
                        if fail_fast:
                            break
                except Exception as e:  # noqa: BLE001 — drill defensivo
                    fail_count += 1
                    falhas.append((nome, f"{descricao} -- exception: {e}"))
                    self.stdout.write(
                        self.style.ERROR(f"  [FAIL] {nome} — exception: {e}")
                    )
                    if fail_fast:
                        break

        total = pass_count + fail_count
        self.stdout.write("")
        self.stdout.write(f"===== Drill SAN-PERFIL-TENANT: {pass_count}/{total} PASS =====")

        if fail_count:
            self.stdout.write(self.style.ERROR(f"{fail_count} FAIL — saneamento incompleto."))
            self.stdout.write("Tarefas P5 Sprint 1 ainda pendentes:")
            for nome, descricao in falhas:
                self.stdout.write(f"  - {nome}: {descricao}")
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("Sprint 1 saneamento estruturalmente OK."))
        self.stdout.write(
            "NOTA: GATE-TENANT-PERFIL-DRILL-PG-REAL Wave A ainda exige rodar "
            "este drill em PG real fresco vs PG ja-M4 (T14 plan.md) — fora do "
            "escopo deste comando."
        )
