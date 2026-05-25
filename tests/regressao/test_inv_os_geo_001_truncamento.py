"""Anti-regressao INV-OS-GEO-001 (T-OS-120a) — truncamento geo LGPD 5a.

INV-OS-GEO-001 item d: coordenada exata persistida em AtividadeDaOS tem
retencao maxima 5 anos pos-conclusao; apos esse prazo geo_lat/long viram
NULL e fica apenas geo_municipio_hash (analitico nao-PII). Job
`truncar_geo_lgpd` (T-OS-091) executa o truncamento.

≥3 testes: happy (dentro de 5a NAO trunca), unhappy (>5a trunca preservando
municipio_hash), cross-tenant (truncamento em tenant A nao afeta B).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import transaction
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.jobs import truncar_geo_lgpd
from src.infrastructure.ordens_servico.models import AtividadeDaOS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory


def _setup(tenant):
    sfx = uuid4().hex[:6]
    with run_in_tenant_context(tenant.id):
        cliente, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento="11222333000181",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": f"Cli {sfx}",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag=f"INV-GEO-{sfx}",
            numero_serie=f"NS-GEO-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_e_pegar_atividade(tenant, cliente, equipamento):
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
        regra_decisao_acordada="default",
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
        atividades = repo.listar_atividades_por_os(res.os_id)
    return atividades[0].id


# =============================================================
# Happy: atividade concluida ha 4 anos NAO eh truncada
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_geo_001_happy_dentro_5a_nao_trunca(db):
    """Happy: concluida ha 4 anos -> geo permanece intacta."""
    tenant = TenantFactory(slug=f"inv-geo-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    ativ_id = _abrir_e_pegar_atividade(tenant, cliente, equipamento)

    with run_in_tenant_context(tenant.id):
        AtividadeDaOS.objects.filter(id=ativ_id).update(
            concluida_em=datetime.now(UTC) - timedelta(days=365 * 4),
            geo_lat=-23.5,
            geo_long=-46.6,
            geo_municipio_hash="hash-sp-4a",
        )
        truncadas = truncar_geo_lgpd(tenant_id=tenant.id)
    assert truncadas == 0

    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.geo_lat == -23.5
        assert ativ.geo_long == -46.6


# =============================================================
# Unhappy: >5a -> lat/long zerados, municipio_hash preservado
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_geo_001_unhappy_passou_5a_zera_lat_long_preserva_hash(db):
    """Unhappy: concluida ha 6 anos -> lat/long NULL; municipio_hash preservado."""
    tenant = TenantFactory(slug=f"inv-geo-u-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    ativ_id = _abrir_e_pegar_atividade(tenant, cliente, equipamento)

    with run_in_tenant_context(tenant.id):
        AtividadeDaOS.objects.filter(id=ativ_id).update(
            concluida_em=datetime.now(UTC) - timedelta(days=365 * 6),
            geo_lat=-23.5,
            geo_long=-46.6,
            geo_municipio_hash="hash-sp-preservar",
        )
        truncadas = truncar_geo_lgpd(tenant_id=tenant.id)
    assert truncadas == 1

    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.geo_lat is None, "lat deveria ter sido truncada"
        assert ativ.geo_long is None, "long deveria ter sido truncada"
        # INV-OS-GEO-001 item d — municipio_hash analitico permanece.
        assert ativ.geo_municipio_hash == "hash-sp-preservar"


# =============================================================
# Cross-tenant: truncamento em tenant A nao afeta tenant B
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_geo_001_cross_tenant_truncamento_isolado(db):
    """Cross-tenant: rodar truncamento em tenant A com atividade vencida
    NAO toca atividade tambem vencida em tenant B."""
    tenant_a = TenantFactory(slug=f"inv-geo-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-geo-ctb-{uuid4().hex[:6]}")
    cli_a, eq_a = _setup(tenant_a)
    cli_b, eq_b = _setup(tenant_b)
    ativ_a = _abrir_e_pegar_atividade(tenant_a, cli_a, eq_a)
    ativ_b = _abrir_e_pegar_atividade(tenant_b, cli_b, eq_b)

    seis_anos_atras = datetime.now(UTC) - timedelta(days=365 * 6)
    with run_in_tenant_context(tenant_a.id):
        AtividadeDaOS.objects.filter(id=ativ_a).update(
            concluida_em=seis_anos_atras, geo_lat=-23.5, geo_long=-46.6
        )
    with run_in_tenant_context(tenant_b.id):
        AtividadeDaOS.objects.filter(id=ativ_b).update(
            concluida_em=seis_anos_atras, geo_lat=-30.0, geo_long=-51.0
        )

    # Roda truncamento somente no tenant A.
    with run_in_tenant_context(tenant_a.id):
        truncadas_a = truncar_geo_lgpd(tenant_id=tenant_a.id)
    assert truncadas_a == 1

    # Tenant B intacto.
    with run_in_tenant_context(tenant_b.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_b)
        assert ativ.geo_lat == -30.0, (
            "tenant B nao deveria ter sido afetado pelo truncamento do tenant A"
        )
        assert ativ.geo_long == -51.0
