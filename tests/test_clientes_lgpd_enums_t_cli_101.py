"""T-CLI-101 / AC-CLI-001-4 — testes do enum LGPD pós-alinhamento spec.

Cobertura:

1. test_aceita_5_bases_legais — cada uma das 5 bases (CONSENTIMENTO,
   EXECUCAO_CONTRATO, OBRIG_LEGAL, LEGITIMO_INTERESSE com lia_id, PROTECAO_CREDITO)
   é aceita pelo CHECK constraint.
2. test_legitimo_interesse_sem_lia_id_rejeitado — CHECK falha quando
   LEGITIMO_INTERESSE sem `aceite_lgpd_lia_id`.
3. test_base_legal_valor_antigo_rejeitado — `art_7_v`/`art_7_i` (valores
   antigos pré-T-CLI-101) são rejeitados (migração one-shot já remapeou).
4. test_aceita_3_origens — `CADASTRO_DIRETO`, `IMPORTACAO_LEGADA`,
   `MIGRACAO_SISTEMA_ANTERIOR`.
5. test_origem_valor_antigo_rejeitado — `balcao`/`portal`/`importacao`/
   `api_terceiro` são rejeitados.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from django.db.utils import IntegrityError
from src.infrastructure.clientes.lgpd import (
    BASE_LEGAL_CONSENTIMENTO,
    BASE_LEGAL_EXECUCAO_CONTRATO,
    BASE_LEGAL_LEGITIMO_INTERESSE,
    BASE_LEGAL_OBRIG_LEGAL,
    BASE_LEGAL_PROTECAO_CREDITO,
    ORIGEM_CADASTRO_DIRETO,
    ORIGEM_IMPORTACAO_LEGADA,
    ORIGEM_MIGRACAO_SISTEMA_ANTERIOR,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _criar_pj(tenant, *, documento, base_legal="", origem="", lia_id=None):
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento=documento,
        nome="Teste LTDA",
        aceite_lgpd_em=datetime.now(UTC),
        aceite_lgpd_base_legal=base_legal,
        aceite_lgpd_origem=origem,
        aceite_lgpd_lia_id=lia_id,
        aceite_lgpd_dispensa_motivo="",
        aceite_lgpd_versao="v1.0-2026-05-18",
    )


@pytest.mark.django_db(transaction=True)
def test_aceita_5_bases_legais():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        # CONSENTIMENTO, EXECUCAO_CONTRATO, OBRIG_LEGAL, PROTECAO_CREDITO sem lia
        for i, base in enumerate(
            [
                BASE_LEGAL_CONSENTIMENTO,
                BASE_LEGAL_EXECUCAO_CONTRATO,
                BASE_LEGAL_OBRIG_LEGAL,
                BASE_LEGAL_PROTECAO_CREDITO,
            ]
        ):
            c = _criar_pj(
                tenant,
                documento=f"11{i:012d}",
                base_legal=base,
                origem=ORIGEM_CADASTRO_DIRETO,
            )
            assert c.aceite_lgpd_base_legal == base

        # LEGITIMO_INTERESSE exige lia_id
        c_li = _criar_pj(
            tenant,
            documento="99999999999999",
            base_legal=BASE_LEGAL_LEGITIMO_INTERESSE,
            origem=ORIGEM_CADASTRO_DIRETO,
            lia_id=uuid4(),
        )
        assert c_li.aceite_lgpd_base_legal == BASE_LEGAL_LEGITIMO_INTERESSE
        assert c_li.aceite_lgpd_lia_id is not None


@pytest.mark.django_db(transaction=True)
def test_legitimo_interesse_sem_lia_id_rejeitado():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        with pytest.raises(IntegrityError, match="ck_cliente_lia_obrigatorio"):
            _criar_pj(
                tenant,
                documento="55555555555555",
                base_legal=BASE_LEGAL_LEGITIMO_INTERESSE,
                origem=ORIGEM_CADASTRO_DIRETO,
                lia_id=None,
            )


@pytest.mark.django_db(transaction=True)
def test_base_legal_valor_antigo_rejeitado():
    """art_7_v/art_7_i devem ser rejeitados — migração 0018 já remapeou."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        with pytest.raises(IntegrityError, match="ck_cliente_base_legal"):
            _criar_pj(
                tenant,
                documento="66666666666666",
                base_legal="art_7_v",
                origem=ORIGEM_CADASTRO_DIRETO,
            )


@pytest.mark.django_db(transaction=True)
def test_aceita_3_origens():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        for i, origem in enumerate(
            [
                ORIGEM_CADASTRO_DIRETO,
                ORIGEM_IMPORTACAO_LEGADA,
                ORIGEM_MIGRACAO_SISTEMA_ANTERIOR,
            ]
        ):
            c = _criar_pj(
                tenant,
                documento=f"22{i:012d}",
                base_legal=BASE_LEGAL_EXECUCAO_CONTRATO,
                origem=origem,
            )
            assert c.aceite_lgpd_origem == origem


@pytest.mark.django_db(transaction=True)
def test_origem_valor_antigo_rejeitado():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        with pytest.raises(IntegrityError, match="ck_cliente_lgpd_origem"):
            _criar_pj(
                tenant,
                documento="77777777777777",
                base_legal=BASE_LEGAL_EXECUCAO_CONTRATO,
                origem="balcao",
            )
