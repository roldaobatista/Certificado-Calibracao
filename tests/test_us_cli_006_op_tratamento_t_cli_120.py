"""T-CLI-120 (AC-CLI-006-7 — LGPD art. 37) — testes
`OperacaoTratamentoCliente` + trigger PG.

Cobertura:

1. test_trigger_grava_cadastro_em_INSERT_cliente — happy path: INSERT
   Cliente dispara INSERT em operacao_tratamento_cliente com
   finalidade=CADASTRO.
2. test_trigger_grava_edicao_em_UPDATE_cliente — UPDATE dispara EDICAO.
3. test_trigger_pega_bulk_update — BLOQ-TL-T4: `.update()` bypassa
   signal Django mas o trigger PG pega (golden).
4. test_trigger_grava_app_usuario_id — usuario do contexto vai pro
   `usuario_id`.
5. test_trigger_payload_inclui_base_legal_e_finalidade_negocial — BLOQ-A7.
6. test_payload_inclui_documento_hash_sem_pii_cru — defesa em
   profundidade contra PII no payload.
7. test_op_tratamento_imutavel_via_codigo_save — INSERT-only.
8. test_op_tratamento_imutavel_via_rls_no_update_no_delete.
9. test_op_tratamento_rls_isolado_por_tenant.
10. test_op_tratamento_check_enum_finalidade.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import IntegrityError, ProgrammingError, connection
from src.infrastructure.audit.models import (
    FinalidadeTratamentoCliente,
    OperacaoTratamentoCliente,
)
from src.infrastructure.clientes.models import Cliente
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)

from tests.factories import TenantFactory


def _criar_cliente(tenant, documento="11144477735") -> Cliente:
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa="PF",
        documento=documento,
        nome="Foo Bar",
        aceite_lgpd_em="2026-05-20T10:00:00Z",
        aceite_lgpd_versao="v1",
        aceite_lgpd_origem="CADASTRO_DIRETO",
        aceite_lgpd_base_legal="EXECUCAO_CONTRATO",
    )


def _contar_op_tratamento(tenant_id, finalidade=None) -> int:
    with run_as_system():
        if finalidade is None:
            return OperacaoTratamentoCliente.objects.filter(tenant_id=tenant_id).count()
        return OperacaoTratamentoCliente.objects.filter(
            tenant_id=tenant_id, finalidade=finalidade
        ).count()


@pytest.mark.django_db(transaction=True)
def test_trigger_grava_cadastro_em_INSERT_cliente():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        _criar_cliente(tenant)
    assert _contar_op_tratamento(tenant.id, "cadastro") == 1


@pytest.mark.django_db(transaction=True)
def test_trigger_grava_edicao_em_UPDATE_cliente():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant)
        cli.nome = "Foo Bar Atualizado"
        cli.save()
    assert _contar_op_tratamento(tenant.id, "cadastro") == 1
    assert _contar_op_tratamento(tenant.id, "edicao") == 1


@pytest.mark.django_db(transaction=True)
def test_trigger_pega_bulk_update():
    """Golden BLOQ-TL-T4 tech-lead: `.update()` bypassa signal Django,
    mas trigger PG pega (defesa em profundidade)."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant)
        # `.update()` é o caminho que signal Django NÃO pega
        Cliente.objects.filter(id=cli.id).update(nome="Via update direto")
    assert _contar_op_tratamento(tenant.id, "edicao") == 1


@pytest.mark.django_db(transaction=True)
def test_trigger_grava_app_usuario_id():
    """`app.usuario_id` do contexto vai pro `usuario_id` da linha."""
    tenant = TenantFactory()
    uid = uuid4()
    with run_in_tenant_context(tenant.id, usuario_id=uid):
        _criar_cliente(tenant)
    with run_as_system():
        linha = OperacaoTratamentoCliente.objects.get(tenant_id=tenant.id)
    assert linha.usuario_id == uid


@pytest.mark.django_db(transaction=True)
def test_trigger_payload_inclui_base_legal_e_finalidade_negocial():
    """BLOQ-A7 advogado: payload registra base_legal + finalidade_negocial."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        _criar_cliente(tenant)
    with run_as_system():
        linha = OperacaoTratamentoCliente.objects.get(tenant_id=tenant.id)
    assert linha.payload["base_legal"] == "EXECUCAO_CONTRATO"
    assert linha.payload["finalidade_negocial"] == "CADASTRO_DIRETO"


@pytest.mark.django_db(transaction=True)
def test_payload_inclui_documento_hash_sem_pii_cru():
    """Documento (CPF/CNPJ) entra como hash SHA-256, não cru."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        _criar_cliente(tenant, documento="11144477735")
    with run_as_system():
        linha = OperacaoTratamentoCliente.objects.get(tenant_id=tenant.id)
    # Hash é hex sha256 (64 chars), não o CPF cru
    assert "11144477735" not in linha.payload["documento_hash"]
    assert len(linha.payload["documento_hash"]) == 64


@pytest.mark.django_db(transaction=True)
def test_op_tratamento_imutavel_via_codigo_save():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        _criar_cliente(tenant)
    with run_as_system():
        linha = OperacaoTratamentoCliente.objects.get(tenant_id=tenant.id)
        linha.finalidade = FinalidadeTratamentoCliente.EXPORT
        with pytest.raises(RuntimeError, match="INSERT-only"):
            linha.save()


@pytest.mark.django_db(transaction=True)
def test_op_tratamento_imutavel_via_rls_no_update_no_delete():
    """Defesa em profundidade — RLS bloqueia UPDATE/DELETE via policy
    (FOR UPDATE USING (false))."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        _criar_cliente(tenant)
    # UPDATE direto via cursor cru — RLS bloqueia
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE operacao_tratamento_cliente "
                "SET finalidade = 'export' WHERE tenant_id = %s",
                [str(tenant.id)],
            )
            # rowcount=0 (policy USING (false) filtra todas as linhas)
            assert cur.rowcount == 0


@pytest.mark.django_db(transaction=True)
def test_op_tratamento_rls_isolado_por_tenant():
    t_a = TenantFactory()
    t_b = TenantFactory()
    with run_in_tenant_context(t_a.id):
        _criar_cliente(t_a, documento="11144477735")
    with run_in_tenant_context(t_b.id):
        _criar_cliente(t_b, documento="52998224725")
    # Em contexto B, SELECT só vê do próprio tenant
    with run_in_tenant_context(t_b.id):
        count = OperacaoTratamentoCliente.objects.count()
    assert count == 1


@pytest.mark.django_db(transaction=True)
def test_op_tratamento_check_enum_finalidade():
    """CHECK constraint rejeita finalidade fora do enum."""
    tenant = TenantFactory()
    with run_as_system():
        with pytest.raises((IntegrityError, ProgrammingError)):
            with connection.cursor() as cur:
                cur.execute(
                    "INSERT INTO operacao_tratamento_cliente "
                    "(id, tenant_id, cliente_id, finalidade, payload, timestamp) "
                    "VALUES (gen_random_uuid(), %s, %s, 'invalida_xyz', '{}'::jsonb, now())",
                    [str(tenant.id), str(uuid4())],
                )
