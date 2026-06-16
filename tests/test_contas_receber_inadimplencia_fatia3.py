"""Fatia 3b — inadimplência perfil-aware (T-CR-043). Verificação 3b (parte 1: adapter).

Cobre o adapter real `TituloVencidoInadimplenciaSource` que substitui o
`SourceListaInterim` do módulo `clientes`:
  - grace por perfil na fronteira exata (D+44 perfil A NÃO entra / D+46 entra);
  - grace menor (perfil D = 7 dias);
  - `InadimplenciaItem` estendido (perfil/grace_perfil) — PLAN-CR-01;
  - cliente anonimizado (cliente_atual_id NULL) fora da régua;
  - `iter_inadimplentes_90d` materializa lista (sem contexto aninhado);
  - `SourceListaInterim` legado aceita os campos novos sem quebrar (PLAN-CR-01);
  - `get_source()` parametrizado por settings.

A notificação D+30/D+45 (T-CR-044) é testada em separado (parte 2).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from django.test import override_settings
from src.domain.comercial.clientes.inadimplencia_source import InadimplenciaItem
from src.domain.contas_receber.entities import Titulo
from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemTitulo,
)
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel
from src.infrastructure.contas_receber.inadimplencia_adapter import (
    TituloVencidoInadimplenciaSource,
    grace_period_inadimplencia_por_perfil,
)
from src.infrastructure.contas_receber.repositories import DjangoTituloRepository
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _hash_cliente() -> str:
    return uuid4().hex + uuid4().hex


def _criar_titulo_vencido(tenant, *, dias_vencido: int, cliente_id, perfil: str) -> Titulo:
    titulo = Titulo(
        titulo_id=uuid4(),
        tenant_id=tenant.id,
        cliente_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=cliente_id, hash_original=_hash_cliente(), key_id="v1"
        ),
        valor_original=Dinheiro(centavos=100000, moeda="BRL"),
        data_emissao=date.today() - timedelta(days=dias_vencido + 30),
        data_vencimento=date.today() - timedelta(days=dias_vencido),
        estado=EstadoTitulo.VENCIDO,
        meio=MeioCobranca.BOLETO,
        categoria_receita=CategoriaReceita.CALIBRACAO_NAO_RBC,
        perfil_no_evento=perfil,
        origem=OrigemTitulo.MANUAL,
        revision=0,
        criado_em=datetime.now(UTC),
    )
    DjangoTituloRepository().salvar_novo_titulo(titulo)
    return titulo


@pytest.mark.django_db(transaction=True)
def test_grace_perfil_a_fronteira_d44_fora_d46_dentro():
    """Perfil A: grace 45 dias. D+44 NÃO entra na régua; D+46 entra (INV-FIN-GRACE-PERFIL-001)."""
    tenant = TenantFactory(perfil_a=True)
    cli_44 = uuid4()
    cli_46 = uuid4()
    with run_in_tenant_context(tenant.id):
        _criar_titulo_vencido(tenant, dias_vencido=44, cliente_id=cli_44, perfil="A")
        _criar_titulo_vencido(tenant, dias_vencido=46, cliente_id=cli_46, perfil="A")
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    clientes = {i.cliente_id for i in items}
    assert cli_46 in clientes  # 46 > grace 45 → entra
    assert cli_44 not in clientes  # 44 < grace 45 → não entra


@pytest.mark.django_db(transaction=True)
def test_grace_perfil_d_curto_d10_entra():
    """Perfil D: grace 7 dias. D+10 entra (grace menor que perfil A)."""
    tenant = TenantFactory(perfil_d=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        _criar_titulo_vencido(tenant, dias_vencido=10, cliente_id=cli, perfil="D")
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    assert cli in {i.cliente_id for i in items}


@pytest.mark.django_db(transaction=True)
def test_item_carrega_perfil_e_grace():
    """InadimplenciaItem estendido (PLAN-CR-01): perfil + grace_perfil preenchidos."""
    tenant = TenantFactory(perfil_a=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        _criar_titulo_vencido(tenant, dias_vencido=50, cliente_id=cli, perfil="A")
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    item = next(i for i in items if i.cliente_id == cli)
    assert item.perfil == "A"
    assert item.grace_perfil == 45
    assert item.dias_vencido == 50


@pytest.mark.django_db(transaction=True)
def test_cliente_anonimizado_fora_da_regua():
    """cliente_atual_id NULL (anonimizado LGPD) não entra na régua de bloqueio."""
    tenant = TenantFactory(perfil_d=True)
    with run_in_tenant_context(tenant.id):
        # título vencido bem além do grace, mas sem cliente_atual_id
        titulo = Titulo(
            titulo_id=uuid4(),
            tenant_id=tenant.id,
            cliente_referencia=ReferenciaPIIAnonimizavel(
                uuid_atual_id=None, hash_original=_hash_cliente(), key_id="v1"
            ),
            valor_original=Dinheiro(centavos=100000, moeda="BRL"),
            data_emissao=date.today() - timedelta(days=120),
            data_vencimento=date.today() - timedelta(days=90),
            estado=EstadoTitulo.VENCIDO,
            meio=MeioCobranca.BOLETO,
            categoria_receita=CategoriaReceita.CALIBRACAO_BASICA,
            perfil_no_evento="D",
            origem=OrigemTitulo.MANUAL,
            revision=0,
            criado_em=datetime.now(UTC),
        )
        DjangoTituloRepository().salvar_novo_titulo(titulo)
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    assert items == []


@pytest.mark.django_db(transaction=True)
def test_grace_period_inadimplencia_por_perfil_le_tenant():
    tenant_a = TenantFactory(perfil_a=True)
    tenant_d = TenantFactory(perfil_d=True)
    assert grace_period_inadimplencia_por_perfil(tenant_a.id) == 45
    assert grace_period_inadimplencia_por_perfil(tenant_d.id) == 7


@pytest.mark.django_db(transaction=True)
def test_iter_inadimplentes_materializa_lista():
    """iter_inadimplentes_90d retorna iterator sobre lista (sem contexto aninhado)."""
    tenant = TenantFactory(perfil_b=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        _criar_titulo_vencido(tenant, dias_vencido=30, cliente_id=cli, perfil="B")
    # Chamado FORA de contexto (como o job faz) — itera tenants internamente.
    items = list(TituloVencidoInadimplenciaSource().iter_inadimplentes_90d())
    assert any(i.cliente_id == cli for i in items)


def test_source_lista_interim_aceita_campos_novos():
    """PLAN-CR-01: SourceListaInterim entrega perfil/grace_perfil sem quebrar."""
    from src.infrastructure.clientes.inadimplencia import SourceListaInterim

    fonte = [
        {
            "tenant_id": str(uuid4()),
            "cliente_id": str(uuid4()),
            "dias_vencido": 95,
            "causation_titulo_id": str(uuid4()),
            "perfil": "A",
            "grace_perfil": 45,
        }
    ]
    with override_settings(INADIMPLENCIA_FONTE_INTERIM=fonte):
        items = list(SourceListaInterim().iter_inadimplentes_90d())
    assert len(items) == 1
    assert items[0].perfil == "A"
    assert items[0].grace_perfil == 45


def test_source_lista_interim_sem_campos_novos_default_none():
    """Deploy parcial: dict sem perfil/grace_perfil → defaults None (não quebra)."""
    from src.infrastructure.clientes.inadimplencia import SourceListaInterim

    fonte = [
        {
            "tenant_id": str(uuid4()),
            "cliente_id": str(uuid4()),
            "dias_vencido": 95,
            "causation_titulo_id": str(uuid4()),
        }
    ]
    with override_settings(INADIMPLENCIA_FONTE_INTERIM=fonte):
        items = list(SourceListaInterim().iter_inadimplentes_90d())
    assert items[0].perfil is None
    assert items[0].grace_perfil is None


@pytest.mark.django_db(transaction=True)
def test_get_source_parametrizado_por_settings():
    from src.infrastructure.clientes.inadimplencia import SourceListaInterim, get_source

    with override_settings(INADIMPLENCIA_SOURCE_IMPL="contas_receber"):
        assert isinstance(get_source(), TituloVencidoInadimplenciaSource)
    with override_settings(INADIMPLENCIA_SOURCE_IMPL="interim"):
        assert isinstance(get_source(), SourceListaInterim)


def test_inadimplencia_item_default_none_isinstance():
    """InadimplenciaItem mantém compat: 4 campos obrigatórios + 2 opcionais."""
    item = InadimplenciaItem(
        tenant_id=UUID(int=1),
        cliente_id=UUID(int=2),
        dias_vencido=95,
        causation_titulo_id=UUID(int=3),
    )
    assert item.perfil is None
    assert item.grace_perfil is None
