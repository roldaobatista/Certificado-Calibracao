"""M5 P2 (T-PAD-010..016) — drill PG-real de schema + RLS + triggers WORM.

Cobre o que o hook estatico nao garante: o COMPORTAMENTO em PG real dos
triggers do modulo `metrologia/padroes`. Padrao TST-004 (happy + unhappy +
cross-campo). Antecipa GATE-PAD-DRILL-LOCAL (P8) com os casos criticos:

- INV-PAD-006 (C-10): incertezas/validade/proximo_recal so mudam dentro do
  fluxo de recal (GUC `app.padrao_recal_em_curso`); UPDATE direto RAISE.
- INV-SOFT-002: DELETE fisico de padrao_metrologico RAISE (soft-delete B).
- VerificacaoIntermediaria / AnaliseCartaControle: append-only (UPDATE+DELETE).
- RecalExternoPadrao: imutavel pos retorno; aprovacao RT one-shot.
- IntercomparacaoPT: inicio imutavel; resultado one-shot pos finalizacao.
- Estrutura: 6 tabelas com RLS+FORCE+4 policies+grants app_user.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from django.db import DatabaseError, connection
from django.utils import timezone
from src.infrastructure.metrologia.padroes.models import (
    AnaliseCartaControle,
    IntercomparacaoPT,
    PadraoMetrologico,
    RecalExternoPadrao,
    VerificacaoIntermediaria,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

TABELAS_M5 = [
    "padrao_metrologico",
    "recal_externo_padrao",
    "verificacao_intermediaria",
    "intercomparacao_pt",
    "analise_carta_controle",
    "vinculo_auxiliar",
]


def _cria_padrao(tenant) -> PadraoMetrologico:
    sfx = uuid4().hex[:8]
    with run_in_tenant_context(tenant.id):
        return PadraoMetrologico.objects.create(
            tenant=tenant,
            numero_serie=f"PAD-{sfx}",
            fabricante="Mettler",
            modelo="XPR",
            vinculacao="INMETRO",
            classe="E2",
            grandezas=[{"simbolo": "kg", "nome": "massa"}],
            faixas=[{"min": "0", "max": "1000", "unidade": "g"}],
            incertezas_certificado=[{"valor": "0.001", "k": "2"}],
            validade_certificado_rastreabilidade=date(2027, 1, 1),
            proximo_recal=date(2027, 1, 1),
            intervalo_recal_meses=12,
            intervalo_vi_meses=3,
            criterio_intervalo="cl. 6.4.7 — historico de estabilidade do padrao",
            vigencia_inicio=timezone.now(),
        )


# =============================================================
# Estrutura — RLS + FORCE + policies + grants (mirror T-CAL-025)
# =============================================================
@pytest.mark.django_db
def test_seis_tabelas_m5_tem_rls_force_e_4_policies():
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON c.relnamespace = n.oid "
            "WHERE n.nspname='public' AND c.relkind='r' AND c.relname = ANY(%s)",
            [TABELAS_M5],
        )
        estado = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
        cur.execute(
            "SELECT tablename, COUNT(*) FROM pg_policies WHERE schemaname='public' "
            "AND tablename = ANY(%s) GROUP BY tablename",
            [TABELAS_M5],
        )
        policies = dict(cur.fetchall())

    faltando = set(TABELAS_M5) - set(estado)
    assert not faltando, f"Tabelas M5 ausentes em PG: {faltando}"
    sem_rls = [t for t, (rls, _force) in estado.items() if not rls]
    sem_force = [t for t, (_rls, force) in estado.items() if not force]
    assert not sem_rls, f"INV-TENANT-001: M5 sem RLS: {sem_rls}"
    assert not sem_force, f"INV-TENANT-002: M5 sem FORCE: {sem_force}"
    incompletas = {t: policies.get(t, 0) for t in TABELAS_M5 if policies.get(t, 0) < 4}
    assert not incompletas, f"M5 com <4 policies RLS: {incompletas}"


@pytest.mark.django_db
def test_app_user_tem_4_grants_nas_6_tabelas_m5():
    with connection.cursor() as cur:
        cur.execute(
            "SELECT table_name, privilege_type FROM information_schema.table_privileges "
            "WHERE table_schema='public' AND grantee='app_user' AND table_name = ANY(%s)",
            [TABELAS_M5],
        )
        grants: dict[str, set[str]] = {}
        for tabela, priv in cur.fetchall():
            grants.setdefault(tabela, set()).add(priv)
    esperado = {"SELECT", "INSERT", "UPDATE", "DELETE"}
    incompletas = {t: esperado - grants.get(t, set()) for t in TABELAS_M5 if esperado - grants.get(t, set())}
    assert not incompletas, f"app_user sem grants completos em M5: {incompletas}"


# =============================================================
# INV-PAD-006 (C-10) — incertezas so via recal (GUC)
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_pad_006_update_incertezas_sem_guc_bloqueia():
    tenant = TenantFactory(slug=f"pad006u-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        PadraoMetrologico.objects.filter(id=padrao.id).update(
            incertezas_certificado=[{"valor": "0.999", "k": "2"}]
        )


@pytest.mark.django_db(transaction=True)
def test_inv_pad_006_update_proximo_recal_sem_guc_bloqueia():
    tenant = TenantFactory(slug=f"pad006r-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        PadraoMetrologico.objects.filter(id=padrao.id).update(proximo_recal=date(2030, 1, 1))


@pytest.mark.django_db(transaction=True)
def test_inv_pad_006_update_incertezas_com_guc_passa():
    tenant = TenantFactory(slug=f"pad006h-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.padrao_recal_em_curso = '1'")
        PadraoMetrologico.objects.filter(id=padrao.id).update(
            incertezas_certificado=[{"valor": "0.002", "k": "2"}],
            proximo_recal=date(2028, 6, 1),
        )
        atual = PadraoMetrologico.objects.get(id=padrao.id)
    assert atual.proximo_recal == date(2028, 6, 1)


@pytest.mark.django_db(transaction=True)
def test_inv_pad_006_update_campo_nao_protegido_passa_sem_guc():
    """estado/descricao mudam livremente (so incertezas/validade/recal sao protegidos)."""
    tenant = TenantFactory(slug=f"pad006np-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        PadraoMetrologico.objects.filter(id=padrao.id).update(descricao="atualizado")
        atual = PadraoMetrologico.objects.get(id=padrao.id)
    assert atual.descricao == "atualizado"


# =============================================================
# INV-SOFT-002 — sem DELETE fisico do padrao
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_soft_002_delete_padrao_bloqueia():
    tenant = TenantFactory(slug=f"padsoft-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        PadraoMetrologico.objects.filter(id=padrao.id).delete()


# =============================================================
# VerificacaoIntermediaria — append-only WORM
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_vi_append_only_update_e_delete_bloqueiam():
    # NOTA: cada statement que levanta erro aborta a transacao PG e faz rollback
    # do bloco inteiro. Por isso o CREATE fica numa transacao limpa (commita ao
    # sair) e cada `raises` fica isolado na sua propria transacao.
    tenant = TenantFactory(slug=f"padvi-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        vi = VerificacaoIntermediaria.objects.create(
            tenant=tenant,
            padrao=padrao,
            data_vi=timezone.now(),
            executor_id_hash="v1$abc",
            metodo_canonicalizado="comparacao com massa padrao classe E1",
            metodo_hash="v1$hash",
            resultado="APROVADO",
        )
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        VerificacaoIntermediaria.objects.filter(id=vi.id).update(resultado="REPROVADO")
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        VerificacaoIntermediaria.objects.filter(id=vi.id).delete()


# =============================================================
# AnaliseCartaControle — append-only WORM (ADR-0070 / INV-PAD-010)
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_analise_carta_append_only_update_bloqueia():
    tenant = TenantFactory(slug=f"padacc-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        acc = AnaliseCartaControle.objects.create(
            tenant=tenant,
            padrao=padrao,
            regra_violada="REGRA_1_FORA_3SIGMA",
            pontos_referenciados_ids=[str(uuid4())],
            linha_central="1.000",
            ucl="1.003",
            lcl="0.997",
            sigma="0.001",
            n_pontos=8,
            janela_meses=24,
            versao_motor_shewhart="shewhart-1.0.0",
            decisao_rt="RECALIBRAR",
            justificativa_canonicalizada="ponto fora de 3 sigma — recalibrar antes de uso",
            justificativa_hash="v1$jh",
        )
        with pytest.raises(DatabaseError):
            AnaliseCartaControle.objects.filter(id=acc.id).update(decisao_rt="ACEITO_COM_JUSTIFICATIVA")


# =============================================================
# RecalExternoPadrao — imutavel pos retorno; aprovacao RT one-shot (C-4)
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_recal_imutavel_pos_retorno_mas_aprovacao_rt_passa_uma_vez():
    tenant = TenantFactory(slug=f"padrec-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        recal = RecalExternoPadrao.objects.create(
            tenant=tenant,
            padrao=padrao,
            enviado_em=timezone.now(),
            lab_externo="Lab RBC X",
            responsavel_envio_id_hash="v1$resp",
            status="RETORNADO",
            retornado_em=timezone.now(),
            incertezas_novas=[{"valor": "0.001", "k": "2"}],
        )
        # aprovacao RT (NULL -> valor) passa uma vez (transacao limpa).
        RecalExternoPadrao.objects.filter(id=recal.id).update(
            aprovado_rt_em=timezone.now(), aprovado_rt_id_hash="v1$rt"
        )
        atual = RecalExternoPadrao.objects.get(id=recal.id)
    assert atual.aprovado_rt_id_hash == "v1$rt"
    # valor retornado e imutavel pos retorno (transacao isolada).
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RecalExternoPadrao.objects.filter(id=recal.id).update(lab_externo="Lab Y")
    # aprovacao RT e one-shot: re-aprovar (aprovado_rt_em ja preenchido) bloqueia.
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RecalExternoPadrao.objects.filter(id=recal.id).update(aprovado_rt_em=timezone.now())


# =============================================================
# IntercomparacaoPT — inicio imutavel; resultado one-shot
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_pt_inicio_imutavel_e_resultado_one_shot():
    tenant = TenantFactory(slug=f"padpt-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        pt = IntercomparacaoPT.objects.create(
            tenant=tenant,
            padrao=padrao,
            lab_organizador="INMETRO",
            protocolo="PT-2026-001",
            data_inicio=timezone.now(),
        )
        # registrar resultado (transicao permitida) finaliza — transacao limpa.
        IntercomparacaoPT.objects.filter(id=pt.id).update(
            resultado="APROVADO", data_resultado=timezone.now(), zeta_score="0.5"
        )
    # inicio sempre imutavel (transacao isolada)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        IntercomparacaoPT.objects.filter(id=pt.id).update(protocolo="PT-OUTRO")
    # resultado congelado pos finalizacao (transacao isolada)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        IntercomparacaoPT.objects.filter(id=pt.id).update(resultado="REJEITADO")
