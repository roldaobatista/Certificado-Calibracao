"""Testes de unit do Cliente.clean() — fechamento Marco 1.

Cobre ramos defensivos do validador (models.py:295-336) que estavam
sem cobertura quando exercitados só via API (validação acontece também
no serializer, então paths do clean() não eram tocados em alguns ramos).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


@pytest.fixture
def tenant(db):
    return TenantFactory(slug=f"clean-{uuid4().hex[:8]}")


@pytest.mark.django_db(transaction=True)
def test_clean_documento_pf_invalido_pela_validacao_mod11(tenant):
    """PF com CPF inválido pelo Mod-11 → ValidationError em `documento`."""
    cliente = Cliente(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PF,
        documento="00000000000",  # inválido pelo Mod-11
        nome="Teste PF",
        aceite_lgpd_em="2026-05-20T10:00:00Z",
        aceite_lgpd_versao="v1",
        aceite_lgpd_origem="CADASTRO_DIRETO",
        aceite_lgpd_base_legal="CONSENTIMENTO",
    )
    with run_in_tenant_context(tenant.id):
        with pytest.raises(ValidationError) as exc:
            cliente.clean()
    assert "documento" in exc.value.message_dict


@pytest.mark.django_db(transaction=True)
def test_clean_pf_sem_aceite_lgpd_rejeita(tenant):
    """PF SEM `aceite_lgpd_em` → ValidationError."""
    cliente = Cliente(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PF,
        documento="11144477735",
        nome="PF Sem Aceite",
        aceite_lgpd_em=None,
    )
    with run_in_tenant_context(tenant.id):
        with pytest.raises(ValidationError) as exc:
            cliente.clean()
    assert "aceite_lgpd_em" in exc.value.message_dict


@pytest.mark.django_db(transaction=True)
def test_clean_pj_sem_aceite_sem_dispensa_rejeita(tenant):
    """PJ SEM aceite E SEM motivo de dispensa → ValidationError."""
    cliente = Cliente(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento="11222333000181",
        nome="PJ Sem Aceite",
        aceite_lgpd_em=None,
        aceite_lgpd_dispensa_motivo="",
    )
    with run_in_tenant_context(tenant.id):
        with pytest.raises(ValidationError) as exc:
            cliente.clean()
    assert "aceite_lgpd_dispensa_motivo" in exc.value.message_dict


@pytest.mark.django_db(transaction=True)
def test_clean_aceite_origem_invalido_rejeita(tenant):
    """Origem fora do enum → ValidationError."""
    cliente = Cliente(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento="11222333000181",
        nome="PJ Origem Bad",
        aceite_lgpd_em="2026-05-20T10:00:00Z",
        aceite_lgpd_versao="v1",
        aceite_lgpd_origem="ORIGEM_NAO_EXISTE",
        aceite_lgpd_base_legal="CONSENTIMENTO",
    )
    with run_in_tenant_context(tenant.id):
        with pytest.raises(ValidationError) as exc:
            cliente.clean()
    assert "aceite_lgpd_origem" in exc.value.message_dict


@pytest.mark.django_db(transaction=True)
def test_clean_pj_com_dispensa_invalida_rejeita(tenant):
    """PJ com `aceite_lgpd_dispensa_motivo` fora do enum → ValidationError."""
    cliente = Cliente(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento="11222333000181",
        nome="PJ Dispensa Bad",
        aceite_lgpd_dispensa_motivo="motivo_inventado",
    )
    with run_in_tenant_context(tenant.id):
        with pytest.raises(ValidationError) as exc:
            cliente.clean()
    assert "aceite_lgpd_dispensa_motivo" in exc.value.message_dict


@pytest.mark.django_db(transaction=True)
def test_clean_pj_com_aceite_origem_valida_passa(tenant):
    """PJ com aceite + origem válida → não rejeita."""
    cliente = Cliente(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento="11222333000181",
        nome="PJ OK",
        aceite_lgpd_em="2026-05-20T10:00:00Z",
        aceite_lgpd_versao="v1",
        aceite_lgpd_origem="CADASTRO_DIRETO",
        aceite_lgpd_base_legal="CONSENTIMENTO",
    )
    with run_in_tenant_context(tenant.id):
        cliente.clean()  # não levanta
