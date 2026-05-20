"""T-CLI-102 / AC-CLI-001-7 — testes do ClienteIdentidadeHistorico.

Rastreabilidade ISO 17025 §7.8.2.1 (b) + §8.4 — alteração de razão social
PJ (mesmo CNPJ) ou nome PF grava linha imutável.

Cobertura:

1. test_update_nome_grava_historico — trigger AFTER UPDATE em clientes
   insere linha em cliente_identidade_historico.
2. test_update_nome_fantasia_grava_historico — idem para nome_fantasia.
3. test_update_outros_campos_nao_grava — UPDATE em campo não-identidade
   (ex: telefone) NÃO gera historico.
4. test_historico_anti_update — trigger BEFORE UPDATE rejeita mutação.
5. test_historico_anti_delete — trigger BEFORE DELETE rejeita exclusão.
6. test_historico_rls_isolado_por_tenant — RLS bloqueia leitura cross-tenant.
7. test_criado_por_id_vem_do_contexto — quando app.usuario_id setado, vai pro campo.
"""

from __future__ import annotations

import pytest
from src.infrastructure.clientes.models import (
    Cliente,
    ClienteIdentidadeHistorico,
    TipoPessoa,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory


def _criar_pj(tenant, *, documento, nome, nome_fantasia=""):
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento=documento,
        nome=nome,
        nome_fantasia=nome_fantasia,
        aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
    )


@pytest.mark.django_db(transaction=True)
def test_update_nome_grava_historico():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c = _criar_pj(tenant, documento="11222333000181", nome="Acme LTDA")
        # antes: zero linhas
        assert ClienteIdentidadeHistorico.objects.filter(cliente_id=c.id).count() == 0
        # UPDATE nome (razão social na JC)
        Cliente.all_objects.filter(id=c.id).update(nome="Acme S.A.")
        # trigger gravou
        linhas = list(
            ClienteIdentidadeHistorico.objects.filter(cliente_id=c.id).order_by("data_efetivacao")
        )
        assert len(linhas) == 1
        h = linhas[0]
        assert h.campo == "nome"
        assert h.valor_anterior == "Acme LTDA"
        assert h.valor_novo == "Acme S.A."
        assert h.tenant_id == tenant.id


@pytest.mark.django_db(transaction=True)
def test_update_nome_fantasia_grava_historico():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c = _criar_pj(
            tenant,
            documento="11222333000181",
            nome="Acme S.A.",
            nome_fantasia="Acme",
        )
        Cliente.all_objects.filter(id=c.id).update(nome_fantasia="Acme Brasil")
        linhas = list(
            ClienteIdentidadeHistorico.objects.filter(cliente_id=c.id).order_by("data_efetivacao")
        )
        assert len(linhas) == 1
        h = linhas[0]
        assert h.campo == "nome_fantasia"
        assert h.valor_anterior == "Acme"
        assert h.valor_novo == "Acme Brasil"


@pytest.mark.django_db(transaction=True)
def test_update_outros_campos_nao_grava():
    """UPDATE em campo fora da identidade (telefone) NÃO dispara trigger."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c = _criar_pj(tenant, documento="11222333000181", nome="Acme")
        Cliente.all_objects.filter(id=c.id).update(telefone="11988887777")
        assert ClienteIdentidadeHistorico.objects.filter(cliente_id=c.id).count() == 0


@pytest.mark.django_db(transaction=True)
def test_historico_anti_update_via_rls_zero_rows():
    """Defesa primária = RLS sem policy UPDATE: `.update()` retorna 0 linhas
    (sem erro). A trigger PG anti-mutation é defesa em profundidade —
    cobertura estrutural em `test_historico_anti_mutation_trigger_existe`."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c = _criar_pj(tenant, documento="11222333000181", nome="Acme")
        Cliente.all_objects.filter(id=c.id).update(nome="Acme S.A.")
        h = ClienteIdentidadeHistorico.objects.filter(cliente_id=c.id).first()
        assert h is not None
        rows_afetadas = ClienteIdentidadeHistorico.objects.filter(id=h.id).update(valor_novo="HACK")
        assert rows_afetadas == 0
        # linha intocada
        assert ClienteIdentidadeHistorico.objects.get(id=h.id).valor_novo == "Acme S.A."


@pytest.mark.django_db(transaction=True)
def test_historico_anti_delete_via_rls_zero_rows():
    """Idem: RLS sem policy DELETE → `.delete()` afeta zero linhas."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c = _criar_pj(tenant, documento="11222333000181", nome="Acme")
        Cliente.all_objects.filter(id=c.id).update(nome="Acme S.A.")
        h = ClienteIdentidadeHistorico.objects.filter(cliente_id=c.id).first()
        assert h is not None
        rows_afetadas, _ = ClienteIdentidadeHistorico.objects.filter(id=h.id).delete()
        assert rows_afetadas == 0
        assert ClienteIdentidadeHistorico.objects.filter(id=h.id).exists()


@pytest.mark.django_db(transaction=True)
def test_historico_anti_mutation_trigger_existe():
    """Triggers BEFORE UPDATE/DELETE de defesa em profundidade existem no
    banco. Qualquer remoção pelo agente IA quebra este teste (alarme
    funcional). Não exercitamos o RAISE porque RLS impede o UPDATE chegar
    na trigger — verificamos a presença estrutural via pg_trigger."""
    from django.db import connection as _conn

    with _conn.cursor() as cur:
        cur.execute(
            "SELECT tgname FROM pg_trigger "
            "WHERE tgname LIKE 'cliente_identidade_historico_anti_%' "
            "AND NOT tgisinternal"
        )
        triggers = sorted(r[0] for r in cur.fetchall())
    assert triggers == [
        "cliente_identidade_historico_anti_delete",
        "cliente_identidade_historico_anti_update",
    ]


@pytest.mark.django_db(transaction=True)
def test_historico_rls_isolado_por_tenant():
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    with run_in_tenant_context(tenant_a.id):
        a = _criar_pj(tenant_a, documento="11222333000181", nome="A")
        Cliente.all_objects.filter(id=a.id).update(nome="A renomeado")
    with run_in_tenant_context(tenant_b.id):
        b = _criar_pj(tenant_b, documento="22333444000172", nome="B")
        Cliente.all_objects.filter(id=b.id).update(nome="B renomeado")
        # Tenant B vê SÓ o histórico dele
        ids_b = set(ClienteIdentidadeHistorico.objects.values_list("cliente_id", flat=True))
        assert ids_b == {b.id}


@pytest.mark.django_db(transaction=True)
def test_criado_por_id_vem_do_contexto():
    tenant = TenantFactory()
    usuario = UsuarioFactory()
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        c = _criar_pj(tenant, documento="11222333000181", nome="Acme")
        Cliente.all_objects.filter(id=c.id).update(nome="Acme S.A.")
        h = ClienteIdentidadeHistorico.objects.filter(cliente_id=c.id).first()
        assert h is not None
        assert h.criado_por_id == usuario.id
