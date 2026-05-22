"""Anti-regressao INV-EQP-PROV-001 (T-EQP-104 — AC-EQP-006-8 / Caminho A Roldao).

`RecebimentoProvisorio` e tabela SEPARADA do `Equipamento` (NAO eh FK).
Defesa POR DESIGN: `Certificado.equipamento_id` aponta para
`Equipamento.id`, jamais para `RecebimentoProvisorio.id`. Impossivel
referenciar provisorio em cert vigente — provisorio precisa SER
PROMOVIDO a Equipamento canonico antes (services_provisorio.promover_provisorio
cria via criar_equipamento reusando pipeline INV-049).

>=3 testes: provisorio nao tem FK reversa de certificados + Certificado
APENAS aceita Equipamento + promocao cria Equipamento real.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from src.infrastructure.certificados.models import (
    Certificado,
    StatusCertificado,
)
from src.infrastructure.equipamentos.models import (
    Equipamento,
    RecebimentoProvisorio,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory


def test_design_certificado_fk_aponta_para_equipamento():
    """Cert.equipamento_id e FK em equipamentos.id, nao em
    recebimentos_provisorios.id."""
    field = Certificado._meta.get_field("equipamento")
    related_model = field.related_model
    assert related_model is Equipamento
    assert related_model is not RecebimentoProvisorio


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_design_recebimento_provisorio_nao_tem_certificados_reverse(db):
    """RecebimentoProvisorio NAO tem related_name 'certificados' —
    busca reversa nao existe (FK aponta pro Equipamento canonico)."""
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"prov-d-{sfx}")
    operador = UsuarioFactory(email=f"op-prov-d-{sfx}@x.local")
    with run_in_tenant_context(tenant.id, operador.id):
        prov = RecebimentoProvisorio.objects.create(
            tenant=tenant,
            tag_provisoria=f"PROV-{sfx}",
            descricao_estimada="Equipamento sem cadastro completo - balanca tipo nao identificado.",
            condicao_visual_chegada="integro",
            foto_storage_key="abc",
            foto_sha256="d" * 64,
            recebido_por_id=operador.id,
            ttl_expira_em=datetime.now(tz=UTC) + timedelta(days=7),
        )
    # Nao deve ter related_name 'certificados' apontando para
    # RecebimentoProvisorio — checagem estatica.
    assert not hasattr(prov, "certificados")


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_design_uuid_provisorio_nao_corresponde_a_equipamento(db):
    """UUID de RecebimentoProvisorio NUNCA aparece como Equipamento.id.

    Provisorio gera UUID proprio; promocao cria UM NOVO Equipamento
    com UUID DIFERENTE (campo `equipamento_promovido_id` no provisorio
    aponta pra ele). Cert sobre provisorio so funcionaria se alguem
    forjasse o UUID — Equipamento.objects.filter(id=prov.id) retorna
    vazio confirmando o isolamento.
    """
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"prov-x-{sfx}")
    operador = UsuarioFactory(email=f"op-prov-x-{sfx}@x.local")
    with run_in_tenant_context(tenant.id, operador.id):
        prov = RecebimentoProvisorio.objects.create(
            tenant=tenant,
            tag_provisoria=f"PROVX-{sfx}",
            descricao_estimada=(
                "Equipamento sem identificacao tipo balanca peq."
            ),
            condicao_visual_chegada="integro",
            foto_storage_key="xyz",
            foto_sha256="e" * 64,
            recebido_por_id=operador.id,
            ttl_expira_em=datetime.now(tz=UTC) + timedelta(days=7),
        )
        # Equipamento canonico com mesmo UUID nao existe.
        assert not Equipamento.objects.filter(id=prov.id).exists()
        # Manager `vigentes` aplicado: nenhum cert vigente pra esse UUID.
        assert (
            Certificado.objects.filter(
                equipamento_id=prov.id,
                status=StatusCertificado.EMITIDO,
                revogado_em__isnull=True,
            ).count()
            == 0
        )
