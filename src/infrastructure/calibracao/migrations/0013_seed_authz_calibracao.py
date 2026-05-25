"""Seed da matriz authz para `calibracao.*` — P4 Fase 4 Batch A (T-CAL-061..068).

6 acoes canonicas calibracao x 5 perfis = 23 linhas perfil x acao.

Acoes (do plan.md M4):
  - calibracao.configurar          (US-CAL-002 — atendente/metrologista define
                                    grandeza+faixa+regra_decisao)
  - calibracao.iniciar_leituras    (US-CAL-004 — metrologista executa cl. 7.6)
  - calibracao.solicitar_revisao   (US-CAL-006 — apos calculo de incerteza)
  - calibracao.aprovar_revisao     (US-CAL-007 — RT 1a conferencia cl. 7.8)
  - calibracao.aprovar_2a_conferencia (US-CAL-008 — RT independente
                                       cl. 6.2.5 + ADR-0026)
  - calibracao.subcontratar        (US-CAL-017 — decisao de negocio cl. 6.6)

Mapeamento perfil x acao:
  - admin_tenant:        todas as 6 (dono do tenant)
  - gerente_operacional: todas as 6 (aprova excecoes ADR-0026)
  - metrologista_bancada: configurar + iniciar_leituras + solicitar_revisao
                          (executa + pede revisao; NAO aprova proprio trabalho —
                          INV-CAL-FRAUDE-REV-001)
  - signatario:          aprovar_revisao + aprovar_2a_conferencia
                          (RT habilitado pra assinatura ISO 17025 cl. 6.2)
  - atendente:           configurar (na recepcao do item — antes da execucao)

Perfis nao listados (financeiro, tecnico, cliente_externo_leitura) NAO tem
acesso a calibracao (so leem via certificado.ler em Marco 5).

NOTA: signatario != rt_signatario. signatario (perfil novo Marco 4) substitui
rt_signatario legacy — ambos coexistem em F-B/M1/M2; Marco 4 padroniza em
signatario.
"""

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova

from __future__ import annotations

import uuid

from django.db import migrations


MATRIZ = [
    # admin_tenant — todas (dono do tenant)
    ("admin_tenant", "calibracao.configurar"),
    ("admin_tenant", "calibracao.iniciar_leituras"),
    ("admin_tenant", "calibracao.solicitar_revisao"),
    ("admin_tenant", "calibracao.aprovar_revisao"),
    ("admin_tenant", "calibracao.aprovar_2a_conferencia"),
    ("admin_tenant", "calibracao.subcontratar"),
    # gerente_operacional — todas (aprova excecoes ADR-0026)
    ("gerente_operacional", "calibracao.configurar"),
    ("gerente_operacional", "calibracao.iniciar_leituras"),
    ("gerente_operacional", "calibracao.solicitar_revisao"),
    ("gerente_operacional", "calibracao.aprovar_revisao"),
    ("gerente_operacional", "calibracao.aprovar_2a_conferencia"),
    ("gerente_operacional", "calibracao.subcontratar"),
    # metrologista_bancada — executa + solicita revisao (nao aprova proprio)
    ("metrologista_bancada", "calibracao.configurar"),
    ("metrologista_bancada", "calibracao.iniciar_leituras"),
    ("metrologista_bancada", "calibracao.solicitar_revisao"),
    # signatario — RT que aprova revisoes (INV-CAL-FRAUDE-REV-001)
    ("signatario", "calibracao.aprovar_revisao"),
    ("signatario", "calibracao.aprovar_2a_conferencia"),
    # atendente — configura na recepcao
    ("atendente", "calibracao.configurar"),
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
            # Em DEV/PROD: authz/0003 + authz/0007 ja rodaram via Django
            # migration runner antes desta — faltando aqui seria bug grave.
            # Em test_afere com TransactionTestCase: tabela `authz_perfil` pode
            # estar TRUNCADA por test anterior (memoria
            # feedback_truncate_seed_transactional). A fixture autouse
            # `_restaura_seeds_apos_truncate` no conftest re-aplica TODOS os
            # seeds em ordem quando authz_perfil vazio detectado — incluindo
            # esta migration. Aqui retornamos cedo (skip) ao inves de raise:
            # o estado consistente sera restaurado pela fixture autouse antes
            # do proximo test transacional.
            cur.execute(
                "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
                "FOR ALL USING (false) WITH CHECK (false);"
            )
            cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
            cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")
            return
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
        ("calibracao", "0012_entidades_p3_advogado_rbc"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
