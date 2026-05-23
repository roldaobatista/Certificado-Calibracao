"""T-OS-010 (cont) - seed inicial dos 6 tipos por tenant existente.

Cria 1 linha por (tenant_id, tipo) com defaults:

| tipo                    | rt | bloq_conc | campo | alerta_h | nc_d |
|-------------------------|----|-----------|-------|----------|------|
| calibracao              | T  | T         | F     | 72       | 15   |
| verificacao_inmetro     | T  | T         | T     | NULL     | NULL |
| manutencao_corretiva    | F  | T         | F     | NULL     | NULL |
| manutencao_preventiva   | F  | T         | F     | NULL     | NULL |
| instalacao              | F  | F         | T     | NULL     | NULL |
| vistoria                | F  | F         | T     | NULL     | NULL |

Notas:
- ADR-0041 matriz tipo x tipo: calibracao, verificacao_inmetro,
  manutencao_corretiva, manutencao_preventiva sao mutuamente exclusivas
  no mesmo equipamento (tipo_bloqueia_concorrencia=True). Instalacao e
  vistoria podem rodar em paralelo (False).
- ADR-0026 cl. 6.2 + INV-CAL-RT-001: calibracao e verificacao_inmetro
  exigem RT competente. Demais nao.
- INV-OS-CAL-LINK-001 + decisao Roldão D-M3-2: defaults RBC perfil A
  (72h alerta / 15 dias NC) so para `calibracao`. Verificacao_inmetro
  nao tem link com modulo Calibracao (eh selo INMETRO direto).

Padrao do seed igual `authz/0007_seed_perfis_marco_3_4.py`:
DISABLE RLS, INSERT idempotente via SELECT-then-INSERT, ENABLE+FORCE RLS.
`atomic = False` exigido pelo DDL no meio do RunPython.

Tenants novos: signal post_save em Tenant (T-OS-029 consumer) replicara
essas 6 entradas. Esta data migration cobre os tenants existentes.
"""

# tests-coverage: tests/test_tipo_atividade_config_seed.py (proximo)

from __future__ import annotations

from django.db import migrations

SEED_DATA = [
    # tipo, requer_rt, bloq_conc, em_campo, alerta_h, nc_d_uteis
    ("calibracao", True, True, False, 72, 15),
    ("verificacao_inmetro", True, True, True, None, None),
    ("manutencao_corretiva", False, True, False, None, None),
    ("manutencao_preventiva", False, True, False, None, None),
    ("instalacao", False, False, True, None, None),
    ("vistoria", False, False, True, None, None),
]


def seed_forward(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        # Pattern v2 RLS bloqueia INSERT cross-tenant sem GUC populado.
        # Desabilita temporariamente pra seed administrativo.
        cur.execute("ALTER TABLE tipo_atividade_config DISABLE ROW LEVEL SECURITY;")

        # Coleta todos os tenant_id existentes via SQL bruto (evita lazy load
        # do ORM que tambem precisa de tenant_ids no GUC).
        cur.execute("SELECT id FROM tenants;")
        tenant_ids = [row[0] for row in cur.fetchall()]

        for tenant_id in tenant_ids:
            for (tipo, rt, bloq, campo, alerta_h, nc_d) in SEED_DATA:
                # Idempotente: se ja existe (re-rodar migration), nao duplica.
                cur.execute(
                    "SELECT id FROM tipo_atividade_config "
                    "WHERE tenant_id = %s AND tipo = %s AND deletado_em IS NULL;",
                    [tenant_id, tipo],
                )
                if cur.fetchone() is not None:
                    continue
                cur.execute(
                    "INSERT INTO tipo_atividade_config ("
                    "  tenant_id, tipo, requer_competencia_rt, tipo_bloqueia_concorrencia, "
                    "  executa_em_campo, prazo_link_calibracao_alerta_h, "
                    "  prazo_link_calibracao_nc_dias_uteis, criado_em, atualizado_em"
                    ") VALUES (%s, %s, %s, %s, %s, %s, %s, now(), now());",
                    [tenant_id, tipo, rt, bloq, campo, alerta_h, nc_d],
                )

        cur.execute("ALTER TABLE tipo_atividade_config ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE tipo_atividade_config FORCE ROW LEVEL SECURITY;")


def seed_reverse(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE tipo_atividade_config DISABLE ROW LEVEL SECURITY;")
        cur.execute(
            "DELETE FROM tipo_atividade_config WHERE tipo IN %s;",
            [tuple(s[0] for s in SEED_DATA)],
        )
        cur.execute("ALTER TABLE tipo_atividade_config ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE tipo_atividade_config FORCE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    atomic = False  # DDL (ALTER TABLE) no meio do RunPython exige

    dependencies = [
        ("ordens_servico", "0003_tipoatividadeconfig"),
    ]

    operations = [
        migrations.RunPython(seed_forward, reverse_code=seed_reverse),
    ]
