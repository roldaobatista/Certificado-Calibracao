"""T-EQP-013 trigger PG (INV-025) + porta CertificadoQueryService.

Cobre:
1. Sem cert vigente: UPDATE em tag/numero_serie/fabricante OK.
2. Com cert vigente: UPDATE em tag bloqueia (texto T1).
3. Com cert vigente: UPDATE em numero_serie bloqueia (texto T2).
4. Com cert vigente: UPDATE em fabricante bloqueia (texto T3).
5. Cert RASCUNHO (nao emitido) nao bloqueia.
6. Cert revogado_em NOT NULL nao bloqueia.
7. UPDATE em campo nao-critico (modelo) OK mesmo com cert vigente.
8. Soft-delete (deletado_em) nao dispara o trigger.
9. RLS cross-tenant — cert de outro tenant invisivel pela porta.
10. `tem_emitido` / `equipamentos_com_cert_vigente`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from django.db.utils import ProgrammingError
from django.utils import timezone
from src.infrastructure.certificados.models import Certificado, StatusCertificado
from src.infrastructure.certificados.query_service import (
    equipamentos_com_cert_vigente,
    tem_emitido,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"cert-{sfx}")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Cert",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag="CERT-001",
            numero_serie="NS-CERT-1",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant": tenant,
        "cliente": cliente,
        "equipamento": equipamento,
    }


def _emitir_cert(tenant, equipamento) -> Certificado:
    return Certificado.objects.create(
        tenant=tenant,
        equipamento=equipamento,
        status=StatusCertificado.EMITIDO,
        emitido_em=timezone.now(),
    )


# ----------------------------------------------------------------------
# Sem cert vigente — UPDATEs livres
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_sem_cert_update_tag_ok(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
            tag="NOVA-TAG-001",
        )
        cenario["equipamento"].refresh_from_db()
    assert cenario["equipamento"].tag == "NOVA-TAG-001"


@pytest.mark.django_db(transaction=True)
def test_sem_cert_update_numero_serie_ok(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
            numero_serie="NOVO-NS",
        )
        cenario["equipamento"].refresh_from_db()
    assert cenario["equipamento"].numero_serie == "NOVO-NS"


# ----------------------------------------------------------------------
# Com cert vigente — INV-025 bloqueia
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_inv_025_t1_tag_bloqueada_com_cert(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        _emitir_cert(cenario["tenant"], cenario["equipamento"])
        with pytest.raises(ProgrammingError, match="INV-025 T1"):
            Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
                tag="MUDANCA-TARDIA",
            )


@pytest.mark.django_db(transaction=True)
def test_inv_025_t2_numero_serie_bloqueada_com_cert(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        _emitir_cert(cenario["tenant"], cenario["equipamento"])
        with pytest.raises(ProgrammingError, match="INV-025 T2"):
            Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
                numero_serie="NS-MUDOU",
            )


@pytest.mark.django_db(transaction=True)
def test_inv_025_t3_fabricante_bloqueada_com_cert(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        _emitir_cert(cenario["tenant"], cenario["equipamento"])
        with pytest.raises(ProgrammingError, match="INV-025 T3"):
            Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
                fabricante="OUTRA-MARCA",
            )


# ----------------------------------------------------------------------
# Cert nao-vigente nao dispara
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_cert_rascunho_nao_bloqueia(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        Certificado.objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            status=StatusCertificado.RASCUNHO,
        )
        # Rascunho nao bloqueia.
        Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
            tag="NOVA-TAG-RASCUNHO-OK",
        )


@pytest.mark.django_db(transaction=True)
def test_cert_revogado_nao_bloqueia(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        Certificado.all_objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            status=StatusCertificado.EMITIDO,
            emitido_em=timezone.now(),
            revogado_em=timezone.now(),  # revogado.
        )
        Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
            tag="NOVA-TAG-POS-REVOGADO",
        )


# ----------------------------------------------------------------------
# Campo nao-critico OK mesmo com cert
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_campo_nao_critico_ok_com_cert(cenario):
    """`modelo` nao e critico (versionavel) — UPDATE livre."""
    with run_in_tenant_context(cenario["tenant"].id):
        _emitir_cert(cenario["tenant"], cenario["equipamento"])
        Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
            modelo="Prix 4 Plus",
        )
        cenario["equipamento"].refresh_from_db()
    assert cenario["equipamento"].modelo == "Prix 4 Plus"


# ----------------------------------------------------------------------
# Soft-delete nao dispara
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_soft_delete_nao_dispara_inv_025(cenario):
    """`deletado_em` setado (com cert) nao deve bloquear — eliminacao
    LGPD precisa funcionar."""
    with run_in_tenant_context(cenario["tenant"].id):
        _emitir_cert(cenario["tenant"], cenario["equipamento"])
        Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
            deletado_em=datetime.now(UTC),
        )


# ----------------------------------------------------------------------
# Porta CertificadoQueryService
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_porta_tem_emitido_true(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        _emitir_cert(cenario["tenant"], cenario["equipamento"])
        assert tem_emitido(cenario["equipamento"].id) is True


@pytest.mark.django_db(transaction=True)
def test_porta_tem_emitido_false_sem_cert(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        assert tem_emitido(cenario["equipamento"].id) is False


@pytest.mark.django_db(transaction=True)
def test_porta_tem_emitido_false_rascunho(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        Certificado.objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            status=StatusCertificado.RASCUNHO,
        )
        assert tem_emitido(cenario["equipamento"].id) is False


@pytest.mark.django_db(transaction=True)
def test_porta_equipamentos_com_cert_vigente_batch(cenario):
    """Cria 2 equipamentos no mesmo tenant; emite cert so num deles;
    porta retorna set com 1 UUID."""
    with run_in_tenant_context(cenario["tenant"].id):
        eq2 = Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="CERT-002",
            numero_serie="NS-CERT-2",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
        _emitir_cert(cenario["tenant"], cenario["equipamento"])
        resultado = equipamentos_com_cert_vigente(
            [cenario["equipamento"].id, eq2.id]
        )
    assert resultado == {cenario["equipamento"].id}


# ----------------------------------------------------------------------
# RLS cross-tenant
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_rls_cross_tenant_cert_invisivel(cenario):
    """Cert de tenant_a invisivel em tenant_b — porta nao consegue
    detectar 'tem_emitido' cross-tenant."""
    with run_in_tenant_context(cenario["tenant"].id):
        _emitir_cert(cenario["tenant"], cenario["equipamento"])
    tenant_b = TenantFactory(slug=f"cert-b-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant_b.id):
        # `tem_emitido` chama Certificado.objects que filtra por
        # default manager (vigentes) + RLS — outro tenant ve 0 linhas.
        assert tem_emitido(cenario["equipamento"].id) is False
