"""Anti-regressao INV-025 (T-EQP-098 — AC-EQP-002-2 / P-EQP-A3).

Trigger PG `equipamento_imutabilidade_pos_cert_trg` (migration
`certificados/0001_initial`) bloqueia mutacao em `tag`, `numero_serie`,
e `fabricante` do `Equipamento` quando ha certificado vigente.

≥3 testes (padrao TST-004): happy (sem cert muta OK) + unhappy
(com cert bloqueia) + cross-campo (3 campos protegidos).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import DatabaseError
from src.infrastructure.certificados.models import (
    Certificado,
    StatusCertificado,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _cria_equipamento(tenant):
    sfx = uuid4().hex[:6]
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome=f"Cli {sfx}",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        return Equipamento.objects.create(
            tenant=tenant,
            tag=f"INV025-{sfx}",
            numero_serie=f"NSI025-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_happy_sem_cert_muta_tag_ok(db):
    tenant = TenantFactory(slug=f"inv025-h-{uuid4().hex[:6]}")
    eq = _cria_equipamento(tenant)
    with run_in_tenant_context(tenant.id):
        Equipamento.objects.filter(id=eq.id).update(tag="INV025-NOVA-TAG")
        eq_atual = Equipamento.objects.get(id=eq.id)
    assert eq_atual.tag == "INV025-NOVA-TAG"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_com_cert_bloqueia_mutacao_de_tag(db):
    tenant = TenantFactory(slug=f"inv025-u-{uuid4().hex[:6]}")
    eq = _cria_equipamento(tenant)
    with run_in_tenant_context(tenant.id):
        Certificado.objects.create(
            tenant=tenant,
            equipamento=eq,
            status=StatusCertificado.EMITIDO,
        )
        with pytest.raises(DatabaseError):
            Equipamento.objects.filter(id=eq.id).update(tag="NOVA-INV025")


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_com_cert_bloqueia_numero_serie_e_fabricante(db):
    tenant = TenantFactory(slug=f"inv025-mc-{uuid4().hex[:6]}")
    eq = _cria_equipamento(tenant)
    with run_in_tenant_context(tenant.id):
        Certificado.objects.create(
            tenant=tenant,
            equipamento=eq,
            status=StatusCertificado.EMITIDO,
        )
        with pytest.raises(DatabaseError):
            Equipamento.objects.filter(id=eq.id).update(numero_serie="NS-X-NEW")
        with pytest.raises(DatabaseError):
            Equipamento.objects.filter(id=eq.id).update(fabricante="Filizola")


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_cross_tenant_cert_de_outro_tenant_nao_bloqueia(db):
    """Cert em tenant B nao protege equipamento em tenant A."""
    tenant_a = TenantFactory(slug=f"inv025-ca-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv025-cb-{uuid4().hex[:6]}")
    eq_a = _cria_equipamento(tenant_a)
    eq_b = _cria_equipamento(tenant_b)
    with run_in_tenant_context(tenant_b.id):
        Certificado.objects.create(
            tenant=tenant_b,
            equipamento=eq_b,
            status=StatusCertificado.EMITIDO,
        )
    # Sem cert no tenant A, mutacao do equipamento de A continua OK.
    with run_in_tenant_context(tenant_a.id):
        Equipamento.objects.filter(id=eq_a.id).update(tag="LIVRE-A")
        assert Equipamento.objects.get(id=eq_a.id).tag == "LIVRE-A"
