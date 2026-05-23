"""Seed da matriz authz para `os.*` — Marco 3 Fase 3 (T-OS-028).

Matriz inicial: 8 acoes canonicas x 5 perfis (admin_tenant,
gerente_operacional, atendente, metrologista_bancada, tecnico).

Decisao de mapeamento de perfis:
- Tasks.md cita perfis "metrologista" e "tecnico_campo"; SEED real
  (`authz/0003_seed_perfis.py` + `authz/0007_seed_perfis_marco_3_4.py`)
  tem `metrologista_bancada` e `tecnico`. Usamos os SEEDADOS — nao
  introduzimos perfil novo aqui (perfis novos exigem migration em
  `authz/` + revisao INV-AUTH-002 expiracao 180d).

Distribuicao das acoes:
- admin_tenant         -> 8 acoes (tudo, dono do tenant)
- gerente_operacional  -> 8 acoes (aprova excecoes — ADR-0026)
- atendente            -> os.abrir + os.adicionar_atividade + os.cancelar
                          (recepcao cadastra; nao executa nem reabre)
- metrologista_bancada -> os.adicionar_atividade + os.iniciar +
                          os.concluir + os.marcar_nc (calibracao no lab)
- tecnico              -> os.iniciar + os.concluir + os.marcar_nc
                          (executor de campo; nao cadastra OS)

Total = 27 linhas perfil x acao. Acoes nao listadas (ex:
`atividade.dispensar_aceite`, `atividade.estender_janela_cal_link`) tem
seed especifico em migrations posteriores (T-OS-079, T-OS-061).
"""

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova

from __future__ import annotations

import uuid

from django.db import migrations

MATRIZ = [
    # admin_tenant — tudo
    ("admin_tenant", "os.abrir"),
    ("admin_tenant", "os.adicionar_atividade"),
    ("admin_tenant", "os.atribuir"),
    ("admin_tenant", "os.iniciar"),
    ("admin_tenant", "os.concluir"),
    ("admin_tenant", "os.marcar_nc"),
    ("admin_tenant", "os.reabrir"),
    ("admin_tenant", "os.cancelar"),
    # gerente_operacional — tudo (ADR-0026 aprovacao de excecao)
    ("gerente_operacional", "os.abrir"),
    ("gerente_operacional", "os.adicionar_atividade"),
    ("gerente_operacional", "os.atribuir"),
    ("gerente_operacional", "os.iniciar"),
    ("gerente_operacional", "os.concluir"),
    ("gerente_operacional", "os.marcar_nc"),
    ("gerente_operacional", "os.reabrir"),
    ("gerente_operacional", "os.cancelar"),
    # atendente — cadastra + cancela (nao executa)
    ("atendente", "os.abrir"),
    ("atendente", "os.adicionar_atividade"),
    ("atendente", "os.cancelar"),
    # metrologista_bancada — executor de calibracao em laboratorio
    ("metrologista_bancada", "os.adicionar_atividade"),
    ("metrologista_bancada", "os.iniciar"),
    ("metrologista_bancada", "os.concluir"),
    ("metrologista_bancada", "os.marcar_nc"),
    # tecnico — executor de campo
    ("tecnico", "os.iniciar"),
    ("tecnico", "os.concluir"),
    ("tecnico", "os.marcar_nc"),
]


def seed(apps, schema_editor):
    """Idempotente: ON CONFLICT DO NOTHING + DISABLE RLS controlado."""
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        cur.execute(
            "SELECT codigo, id FROM authz_perfil "
            "WHERE codigo = ANY(%s) AND tenant_id IS NULL;",
            [list({p for p, _ in MATRIZ})],
        )
        perfil_id_por_codigo = dict(cur.fetchall())
        faltando = {p for p, _ in MATRIZ} - set(perfil_id_por_codigo)
        if faltando:
            raise RuntimeError(
                f"Perfis seedados nao encontrados: {sorted(faltando)} — "
                "rode authz/0003 + authz/0007 antes desta migration."
            )
        for perfil_codigo, acao in MATRIZ:
            perfil_id = perfil_id_por_codigo[perfil_codigo]
            cur.execute(
                "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                "VALUES (%s, %s, %s, TRUE, now()) "
                "ON CONFLICT (perfil_id, acao) DO NOTHING;",
                [str(uuid.uuid4()), perfil_id, acao],
            )
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


def unseed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        cur.execute(
            "DELETE FROM authz_perfil_acao WHERE acao = ANY(%s);",
            [list({a for _, a in MATRIZ})],
        )
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("ordens_servico", "0012_nao_conformidade_e_sla"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
