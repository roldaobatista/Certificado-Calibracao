"""Seed authz das acoes `calibracao.*` que faltavam para a porta REST do Marco 4
(consolidacao da base pos-bloco-metrologia — fecha GATE-CAL-SEG "10 ViewSets
ACTION_MAP" + GATE-CAL-VIEWSETS-WAVE-A).

Contexto (regra #0): os ViewSets M4 ja existentes (Calibracao/Leitura/Revisao/
Conferencia/NaoConformidade/Reclamacao) eram "esqueleto Wave A" — nunca tiveram
`get_authz_action`/`ACTION_MAP` nem as acoes seedadas. Sem isso `RequireAuthz`
nega-por-default e a porta de rede do M4 fica fechada. A 0013 seedou so 6 acoes
(configurar/iniciar_leituras/solicitar_revisao/aprovar_revisao/
aprovar_2a_conferencia/subcontratar); a 0021 acrescentou
registrar_recebimento_subcontratado. Esta migration acrescenta as 13 restantes.

Mapeamento perfil x acao (derivado da logica da 0013 + papeis ISO 17025):
  - calibracao.ler                       leitura ampla da operacao (todos os 5 perfis)
  - calibracao.recepcionar               intake do item (atendente + gestao)
  - calibracao.cancelar                  decisao de gestao
  - calibracao.registrar_leitura         execucao da medicao cl. 7.6 (metrologista)
  - calibracao.corrigir_leitura          rasura digital cl. 7.5 (metrologista)
  - calibracao.rejeitar_revisao          par de aprovar_revisao (signatario/RT)
  - calibracao.avaliar_conformidade      regra de decisao cl. 7.8.6 (metrologista/RT)
  - calibracao.calcular_orcamento_incerteza  orcamento GUM (metrologista)
  - calibracao.nc_abrir                  qualquer um da operacao marca NC
  - calibracao.nc_fechar                 gestao da qualidade fecha
  - calibracao.reclamacao_abrir          recebe do cliente (atendente + gestao)
  - calibracao.reclamacao_atribuir_rt    gestao designa RT independente
  - calibracao.reclamacao_responder      RT responde (signatario)

Perfis: admin_tenant / gerente_operacional / metrologista_bancada / signatario /
atendente (todos NULL-tenant, seedados em authz/0007). Separacao de funcoes
metrologica (executor != revisor/conferente, recebedor != executor) continua
enforcada nos use cases — authz e a 1a barreira, nao a unica.

Idempotente (ON CONFLICT DO NOTHING) + tratamento TransactionTestCase truncate
identico a 0013/0021 (memoria feedback_truncate_seed_transactional).
"""

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova

from __future__ import annotations

import uuid

from django.db import migrations

_ADMIN = "admin_tenant"
_GER = "gerente_operacional"
_MET = "metrologista_bancada"
_SIG = "signatario"
_ATD = "atendente"

MATRIZ = [
    # leitura ampla (read-path retrieve)
    (_ADMIN, "calibracao.ler"),
    (_GER, "calibracao.ler"),
    (_MET, "calibracao.ler"),
    (_SIG, "calibracao.ler"),
    (_ATD, "calibracao.ler"),
    # recepcao do item
    (_ADMIN, "calibracao.recepcionar"),
    (_GER, "calibracao.recepcionar"),
    (_ATD, "calibracao.recepcionar"),
    # cancelamento (gestao)
    (_ADMIN, "calibracao.cancelar"),
    (_GER, "calibracao.cancelar"),
    # execucao da medicao
    (_ADMIN, "calibracao.registrar_leitura"),
    (_GER, "calibracao.registrar_leitura"),
    (_MET, "calibracao.registrar_leitura"),
    # rasura digital cl. 7.5
    (_ADMIN, "calibracao.corrigir_leitura"),
    (_GER, "calibracao.corrigir_leitura"),
    (_MET, "calibracao.corrigir_leitura"),
    # rejeitar revisao (par de aprovar_revisao — signatario/RT)
    (_ADMIN, "calibracao.rejeitar_revisao"),
    (_GER, "calibracao.rejeitar_revisao"),
    (_SIG, "calibracao.rejeitar_revisao"),
    # regra de decisao cl. 7.8.6
    (_ADMIN, "calibracao.avaliar_conformidade"),
    (_GER, "calibracao.avaliar_conformidade"),
    (_MET, "calibracao.avaliar_conformidade"),
    (_SIG, "calibracao.avaliar_conformidade"),
    # orcamento de incerteza GUM
    (_ADMIN, "calibracao.calcular_orcamento_incerteza"),
    (_GER, "calibracao.calcular_orcamento_incerteza"),
    (_MET, "calibracao.calcular_orcamento_incerteza"),
    # nao-conformidade — abrir (qualquer operacao) / fechar (gestao)
    (_ADMIN, "calibracao.nc_abrir"),
    (_GER, "calibracao.nc_abrir"),
    (_MET, "calibracao.nc_abrir"),
    (_SIG, "calibracao.nc_abrir"),
    (_ADMIN, "calibracao.nc_fechar"),
    (_GER, "calibracao.nc_fechar"),
    # reclamacao do cliente (US-CAL-018)
    (_ADMIN, "calibracao.reclamacao_abrir"),
    (_GER, "calibracao.reclamacao_abrir"),
    (_ATD, "calibracao.reclamacao_abrir"),
    (_ADMIN, "calibracao.reclamacao_atribuir_rt"),
    (_GER, "calibracao.reclamacao_atribuir_rt"),
    (_ADMIN, "calibracao.reclamacao_responder"),
    (_GER, "calibracao.reclamacao_responder"),
    (_SIG, "calibracao.reclamacao_responder"),
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
            # test_afere + TransactionTestCase: authz_perfil pode estar TRUNCADA;
            # a fixture autouse _restaura_seeds_apos_truncate re-aplica os seeds
            # em ordem. Skip (early return) ao inves de raise (paralelo 0013/0021).
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
        ("calibracao", "0021_seed_authz_registrar_recebimento"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
