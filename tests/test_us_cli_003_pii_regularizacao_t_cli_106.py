"""T-CLI-106 (AC-CLI-003-7) — testes de estado restrito + regularização.

Cobertura:
1. test_cliente_importado_legada_inicia_restrito
2. test_cliente_cadastro_direto_NAO_restrito
3. test_cliente_migracao_sistema_anterior_NAO_restrito
4. test_consentimento_revogado_com_base_consentimento_vira_restrito
5. test_regularizar_aceite_legado_sai_do_estado_restrito
6. test_regularizar_aceite_legado_idempotente
7. test_regularizar_rejeita_origem_nao_legada
"""

from __future__ import annotations

import pytest
from src.infrastructure.clientes.estado_restrito import (
    cliente_em_estado_restrito,
    regularizar_aceite_legado,
)
from src.infrastructure.clientes.models import Cliente
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _criar_cliente(tenant, *, origem, base="EXECUCAO_CONTRATO") -> Cliente:
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa="PF",
        documento="11144477735",
        nome="Foo",
        aceite_lgpd_em="2026-05-20T10:00:00Z",
        aceite_lgpd_versao="v1",
        aceite_lgpd_origem=origem,
        aceite_lgpd_base_legal=base,
    )


@pytest.mark.django_db(transaction=True)
def test_cliente_importado_legada_inicia_restrito():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant, origem="IMPORTACAO_LEGADA")
    assert cliente_em_estado_restrito(cli) is True
    assert cli.pii_regularizacao_em is None


@pytest.mark.django_db(transaction=True)
def test_cliente_cadastro_direto_NAO_restrito():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant, origem="CADASTRO_DIRETO")
    assert cliente_em_estado_restrito(cli) is False


@pytest.mark.django_db(transaction=True)
def test_cliente_migracao_sistema_anterior_NAO_restrito():
    """MIGRACAO_SISTEMA_ANTERIOR já vem com aceite — não é estado restrito."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant, origem="MIGRACAO_SISTEMA_ANTERIOR")
    assert cliente_em_estado_restrito(cli) is False


@pytest.mark.django_db(transaction=True)
def test_consentimento_revogado_com_base_consentimento_vira_restrito():
    """T-CLI-115 + T-CLI-106 integração: revogação coloca em restrito
    se a base atual era CONSENTIMENTO."""
    from datetime import UTC, datetime

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant, origem="CADASTRO_DIRETO", base="CONSENTIMENTO")
        cli.consentimento_revogado_em = datetime.now(UTC)
        cli.save()
    assert cliente_em_estado_restrito(cli) is True


@pytest.mark.django_db(transaction=True)
def test_regularizar_aceite_legado_sai_do_estado_restrito():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant, origem="IMPORTACAO_LEGADA")
        assert cliente_em_estado_restrito(cli) is True
        regularizar_aceite_legado(cli)
        cli.refresh_from_db()
    assert cli.pii_regularizacao_em is not None
    assert cliente_em_estado_restrito(cli) is False


@pytest.mark.django_db(transaction=True)
def test_regularizar_aceite_legado_idempotente():
    """Chamar 2x não dobra o timestamp."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant, origem="IMPORTACAO_LEGADA")
        regularizar_aceite_legado(cli)
        ts_primeiro = cli.pii_regularizacao_em
        regularizar_aceite_legado(cli)
        cli.refresh_from_db()
    assert cli.pii_regularizacao_em == ts_primeiro


@pytest.mark.django_db(transaction=True)
def test_regularizar_rejeita_origem_nao_legada():
    """Tentar regularizar cliente CADASTRO_DIRETO levanta ValueError."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant, origem="CADASTRO_DIRETO")
        with pytest.raises(ValueError, match="não tem origem=IMPORTACAO_LEGADA"):
            regularizar_aceite_legado(cli)
