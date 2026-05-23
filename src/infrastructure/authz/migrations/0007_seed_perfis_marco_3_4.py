"""Seed perfis Marco 3 (OS) + Marco 4 (Calibração) — idempotente.

Refs: ADR-0012 (autorização unificada), ADR-0023 (OS com atividades),
ADR-0022 (RT tenant), INV-AUTHZ-001..004, INV-AUTH-002 (perfis sensíveis).

Achado-raiz: F-B-C1 (Onda 3 saneamento pré-Marco 3) — Auditor 2 detectou que
perfil `financeiro` foi citado em PRD-financeiro/billing-saas/fiscal sem nunca
ser seedado. Mesma situação pra metrologista_bancada (Marco 4 calibração),
atendente (Marco 3 OS — abre ticket), gerente_operacional (Marco 3 OS — aprova
exceção 2ª conferência ADR-0026) e signatario (Marco 4 — emite certificado).

5 novos perfis (todos globais — `tenant_id IS NULL`):

- `financeiro`        — fatura.criar, fatura.estornar, contas_receber.*, contas_pagar.*
- `metrologista_bancada` — os.ler, atividade.executar (calibração), cert.preparar
- `atendente`         — os.criar, os.ler, cliente.ler, cliente.atualizar
- `gerente_operacional` — os.*, exceção_2a_conferencia.aprovar (ADR-0026)
- `signatario`        — os.ler, certificado.emitir, certificado.republicar

Matriz inicial (subset — completar conforme Marcos 3/4 entregarem AC):
- 19 linhas perfil × ação cobrindo cenários E2E críticos.

Perfis sensíveis (INV-AUTH-002 §expiração 180d + INV-AUTH-004 troca 90d):
financeiro, signatario, metrologista_bancada, gerente_operacional, admin_tenant
(este último já seedado em 0003).
"""

# tests-coverage: tests/test_perfis_marco_3_4_seed.py (Wave A)

from __future__ import annotations

import uuid

from django.db import migrations

PERFIS = [
    ("financeiro", "Financeiro (fatura, contas, conciliação)"),
    ("metrologista_bancada", "Metrologista de Bancada (calibração — Marco 4)"),
    ("atendente", "Atendente (recepção, abertura de OS — Marco 3)"),
    ("gerente_operacional", "Gerente Operacional (aprova exceções operacionais)"),
    ("signatario", "Signatário ISO 17025 (emite certificado — Marco 4)"),
]

# Matriz inicial perfil × ação. Cobre cenários canônicos dos Marcos 3 e 4.
# Cada nova ação introduzida por US-OS-* / US-CAL-* será adicionada em migration
# posterior (uma por entrega de marco) — esta seed é a "linha de base".
MATRIZ = [
    # financeiro — opera financeiro, lê OS pra contexto de cobrança
    ("financeiro", "fatura.criar", True),
    ("financeiro", "fatura.estornar", True),
    ("financeiro", "contas_receber.ler", True),
    ("financeiro", "contas_receber.baixar", True),
    ("financeiro", "os.ler", True),
    # metrologista_bancada — Marco 4 calibração
    ("metrologista_bancada", "os.ler", True),
    ("metrologista_bancada", "atividade.executar", True),
    ("metrologista_bancada", "certificado.preparar", True),
    # atendente — Marco 3 OS, lê + atualiza cliente
    ("atendente", "os.criar", True),
    ("atendente", "os.ler", True),
    ("atendente", "cliente.ler", True),
    ("atendente", "cliente.atualizar", True),
    # gerente_operacional — aprovação de exceções + visão ampla
    ("gerente_operacional", "os.criar", True),
    ("gerente_operacional", "os.ler", True),
    ("gerente_operacional", "atividade.executar", True),
    ("gerente_operacional", "excecao_2a_conferencia.aprovar", True),
    # signatario — assina certificado (substitui rt_signatario com escopo Marco 4)
    ("signatario", "os.ler", True),
    ("signatario", "certificado.emitir", True),
    ("signatario", "certificado.republicar", True),
]


def seed(apps, schema_editor):
    """INSERT idempotente — não recria perfil/matriz já existente."""
    perfil_ids: dict[str, str] = {}

    with schema_editor.connection.cursor() as cur:
        # Mesmo padrão de 0003_seed_perfis.py: app_migrator é NOBYPASSRLS, então
        # precisa desabilitar RLS + dropar policy de bloqueio pra inserir, e
        # depois recriar policy + reabilitar RLS.
        cur.execute("ALTER TABLE authz_perfil DISABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_block_mutation ON authz_perfil;")
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )

        for codigo, nome in PERFIS:
            # idempotência: se perfil já existe (re-rodar migration manual), reusa id
            cur.execute(
                "SELECT id FROM authz_perfil WHERE codigo = %s AND tenant_id IS NULL;",
                [codigo],
            )
            row = cur.fetchone()
            if row is not None:
                perfil_ids[codigo] = str(row[0])
                continue
            pid = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO authz_perfil (id, codigo, nome, descricao, tenant_id, criado_em) "
                "VALUES (%s, %s, %s, '', NULL, now());",
                [pid, codigo, nome],
            )
            perfil_ids[codigo] = pid

        for perfil_codigo, acao, pode in MATRIZ:
            # idempotência: se par (perfil, acao) já existe, pula
            cur.execute(
                "SELECT 1 FROM authz_perfil_acao "
                "WHERE perfil_id = %s AND acao = %s;",
                [perfil_ids[perfil_codigo], acao],
            )
            if cur.fetchone() is not None:
                continue
            cur.execute(
                "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                "VALUES (%s, %s, %s, %s, now());",
                [str(uuid.uuid4()), perfil_ids[perfil_codigo], acao, pode],
            )

        # policy-test-coverage: skip -- recriacao identica da policy droppada acima neste mesmo seed; cobertura em 0002_rls_e_trigger.py + tests/test_authz_isolamento.py
        cur.execute(
            "CREATE POLICY authz_perfil_block_mutation ON authz_perfil "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil FORCE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


def unseed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil DISABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_block_mutation ON authz_perfil;")
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        cur.execute(
            "DELETE FROM authz_perfil_acao WHERE perfil_id IN "
            "(SELECT id FROM authz_perfil WHERE codigo IN %s AND tenant_id IS NULL);",
            [tuple(p[0] for p in PERFIS)],
        )
        cur.execute(
            "DELETE FROM authz_perfil WHERE codigo IN %s AND tenant_id IS NULL;",
            [tuple(p[0] for p in PERFIS)],
        )
        # policy-test-coverage: skip -- recriacao identica de policy de bloqueio no rollback
        cur.execute(
            "CREATE POLICY authz_perfil_block_mutation ON authz_perfil "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil FORCE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    # atomic=False — mesmo motivo de 0003 (ALTER + INSERT + ALTER no mesmo migration)
    atomic = False

    dependencies = [
        ("authz", "0006_authzdecision_ip_hash_textfield"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
