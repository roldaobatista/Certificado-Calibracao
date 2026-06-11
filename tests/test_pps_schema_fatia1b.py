"""Frente `produtos-pecas-servicos` — Fatia 1b (T-PPS-024): schema PG-real.

Cobre o COMPORTAMENTO que o drill estrutural não garante:
- RLS FORCE + policies + isolamento cross-tenant nas 5 tabelas (INV-TENANT-001/002).
- INV-PPS-CODIGO-UNICO (409 via UNIQUE); 1 tabela padrão (UNIQUE parcial).
- INV-PPS-VERSAO-IMUTAVEL / INV-PPS-LINHA-IMUTAVEL: UPDATE de campo probatório
  RAISE; DELETE físico RAISE; vigencia_fim/revogado_em one-shot.
- INV-PPS-*-SEM-SOBREPOSICAO: exclusion btree_gist (overlap RAISE; revogada +
  substituta mesma janela OK — lição M2 em PG real).
- CHECK preco > 0 (TL-PPS-16 — sentinela 0 da OS preservada no banco).

Cada RAISE aborta a transação PG → cenários isolados (TST-004).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.produtos_pecas_servicos.models import (
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaTabelaPreco,
    TabelaPreco,
)

from tests.factories import TenantFactory

TABELAS = (
    "item_catalogo",
    "item_catalogo_versao",
    "kit_composicao",
    "tabela_preco",
    "linha_tabela_preco",
)

_JAN = datetime(2026, 1, 1, tzinfo=UTC)
_JUN = datetime(2026, 6, 1, tzinfo=UTC)


def _cria_item(tenant, *, codigo="P-001", tipo="peca") -> ItemCatalogo:
    with run_in_tenant_context(tenant.id):
        return ItemCatalogo.objects.create(
            tenant=tenant, codigo_interno=codigo, tipo=tipo,
            controla_estoque=tipo != "servico",
        )


def _cria_versao(tenant, item, *, n=1, preco="50.00", inicio=_JAN, fim=None) -> ItemCatalogoVersao:
    with run_in_tenant_context(tenant.id):
        return ItemCatalogoVersao.objects.create(
            tenant=tenant, item=item, versao_n=n, nome="Peça X", unidade_medida="un",
            preco_padrao=Decimal(preco), vigencia_inicio=inicio, vigencia_fim=fim,
            criado_por=uuid4(),
        )


def _cria_tabela(tenant, *, nome="Padrão", eh_padrao=True) -> TabelaPreco:
    with run_in_tenant_context(tenant.id):
        return TabelaPreco.objects.create(tenant=tenant, nome=nome, eh_padrao=eh_padrao)


def _cria_linha(tenant, tabela, item, *, preco="55.00", inicio=_JAN, fim=None) -> LinhaTabelaPreco:
    with run_in_tenant_context(tenant.id):
        return LinhaTabelaPreco.objects.create(
            tenant=tenant, tabela=tabela, item=item, preco=Decimal(preco),
            vigencia_inicio=inicio, vigencia_fim=fim, criado_por=uuid4(),
        )


# === estrutura RLS (INV-TENANT-001/002) ===


@pytest.mark.django_db
def test_rls_force_e_4_policies_nas_5_tabelas() -> None:
    with connection.cursor() as cur:
        for tabela in TABELAS:
            cur.execute(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON c.relnamespace=n.oid "
                "WHERE n.nspname='public' AND c.relname=%s",
                [tabela],
            )
            enabled, forced = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [tabela])
            n_pol = cur.fetchone()[0]
            assert enabled, f"INV-TENANT-001: {tabela} sem RLS"
            assert forced, f"INV-TENANT-002: {tabela} sem FORCE"
            assert n_pol >= 4, f"{tabela} com <4 policies ({n_pol})"


@pytest.mark.django_db(transaction=True)
def test_rls_isola_as_5_tabelas_entre_tenants() -> None:
    """UNHAPPY cross-tenant nas 5 tabelas (lição B1 da frente #1 — desde o início)."""
    tenant_a, tenant_b = TenantFactory(), TenantFactory()
    item = _cria_item(tenant_a)
    versao = _cria_versao(tenant_a, item)
    filho = _cria_item(tenant_a, codigo="P-002")
    kit = _cria_item(tenant_a, codigo="K-001", tipo="kit")
    with run_in_tenant_context(tenant_a.id):
        comp = KitComposicao.objects.create(
            tenant=tenant_a, kit_item=kit, item_filho=filho, quantidade=Decimal("1")
        )
    tabela = _cria_tabela(tenant_a)
    linha = _cria_linha(tenant_a, tabela, item)

    with run_in_tenant_context(tenant_b.id):
        assert not ItemCatalogo.objects.filter(id=item.id).exists()
        assert not ItemCatalogoVersao.objects.filter(id=versao.id).exists()
        assert not KitComposicao.objects.filter(id=comp.id).exists()
        assert not TabelaPreco.objects.filter(id=tabela.id).exists()
        assert not LinhaTabelaPreco.objects.filter(id=linha.id).exists()

    with run_in_tenant_context(tenant_a.id):
        assert ItemCatalogo.objects.filter(id=item.id).exists()
        assert LinhaTabelaPreco.objects.filter(id=linha.id).exists()


# === UNIQUEs de negócio ===


@pytest.mark.django_db(transaction=True)
def test_codigo_interno_duplicado_no_tenant_raise() -> None:
    tenant = TenantFactory()
    _cria_item(tenant, codigo="P-001")
    with pytest.raises(IntegrityError):
        _cria_item(tenant, codigo="P-001")


@pytest.mark.django_db(transaction=True)
def test_codigo_igual_em_tenants_diferentes_ok() -> None:
    i1 = _cria_item(TenantFactory(), codigo="P-001")
    i2 = _cria_item(TenantFactory(), codigo="P-001")
    assert i1.id != i2.id


@pytest.mark.django_db(transaction=True)
def test_segunda_tabela_padrao_raise() -> None:
    tenant = TenantFactory()
    _cria_tabela(tenant, nome="Padrão")
    with pytest.raises(IntegrityError):
        _cria_tabela(tenant, nome="Outra padrão")
    # Não-padrão adicional é permitido (schema N-tabelas — D-PPS-3).
    _cria_tabela(tenant, nome="Atacado V2", eh_padrao=False)


# === CHECK preco > 0 (TL-PPS-16) ===


@pytest.mark.django_db(transaction=True)
def test_preco_zero_raise_no_banco() -> None:
    tenant = TenantFactory()
    item = _cria_item(tenant)
    with pytest.raises(IntegrityError):
        _cria_versao(tenant, item, preco="0.00")
    tabela = _cria_tabela(tenant)
    with pytest.raises(IntegrityError):
        _cria_linha(tenant, tabela, item, preco="0.00")


# === INV-PPS-VERSAO-IMUTAVEL / INV-PPS-LINHA-IMUTAVEL (triggers 0003) ===


@pytest.mark.django_db(transaction=True)
def test_update_direto_preco_da_versao_raise() -> None:
    tenant = TenantFactory()
    versao = _cria_versao(tenant, _cria_item(tenant))
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        ItemCatalogoVersao.objects.filter(id=versao.id).update(preco_padrao=Decimal("99.00"))


@pytest.mark.django_db(transaction=True)
def test_update_direto_preco_da_linha_raise() -> None:
    tenant = TenantFactory()
    item = _cria_item(tenant)
    linha = _cria_linha(tenant, _cria_tabela(tenant), item)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        LinhaTabelaPreco.objects.filter(id=linha.id).update(preco=Decimal("99.00"))


@pytest.mark.django_db(transaction=True)
def test_delete_fisico_de_versao_e_linha_raise() -> None:
    tenant = TenantFactory()
    item = _cria_item(tenant)
    versao = _cria_versao(tenant, item)
    linha = _cria_linha(tenant, _cria_tabela(tenant), item)
    with run_in_tenant_context(tenant.id):
        with pytest.raises(DatabaseError):
            ItemCatalogoVersao.objects.filter(id=versao.id).delete()
        with pytest.raises(DatabaseError):
            LinhaTabelaPreco.objects.filter(id=linha.id).delete()


@pytest.mark.django_db(transaction=True)
def test_vigencia_fim_e_revogacao_one_shot() -> None:
    tenant = TenantFactory()
    linha = _cria_linha(tenant, _cria_tabela(tenant), _cria_item(tenant))
    with run_in_tenant_context(tenant.id):
        # encerramento NULL→data OK
        LinhaTabelaPreco.objects.filter(id=linha.id).update(vigencia_fim=_JUN)
        # re-escrita do fim → RAISE
        with pytest.raises(DatabaseError):
            LinhaTabelaPreco.objects.filter(id=linha.id).update(
                vigencia_fim=_JUN + timedelta(days=30)
            )
    with run_in_tenant_context(tenant.id):
        LinhaTabelaPreco.objects.filter(id=linha.id).update(
            revogado_em=timezone.now(), motivo_revogacao="linha errada corrigida"
        )
        with pytest.raises(DatabaseError):
            LinhaTabelaPreco.objects.filter(id=linha.id).update(
                motivo_revogacao="mudando o motivo depois"
            )


# === não-sobreposição (exclusions 0004) + lição M2 em PG real ===


@pytest.mark.django_db(transaction=True)
def test_versoes_sobrepostas_raise_e_revogada_libera_espaco() -> None:
    tenant = TenantFactory()
    item = _cria_item(tenant)
    _cria_versao(tenant, item, n=1, inicio=_JAN)  # aberta (+inf)
    with pytest.raises(IntegrityError):
        _cria_versao(tenant, item, n=2, inicio=_JUN)  # sobrepõe a aberta
    # Revogar a v1 libera o espaço (WHERE revogado_em IS NULL).
    with run_in_tenant_context(tenant.id):
        ItemCatalogoVersao.objects.filter(item=item, versao_n=1).update(
            revogado_em=timezone.now(), motivo_revogacao="preco digitado errado"
        )
    substituta = _cria_versao(tenant, item, n=2, inicio=_JAN)  # MESMA janela OK
    assert substituta.versao_n == 2


@pytest.mark.django_db(transaction=True)
def test_linhas_sobrepostas_raise_por_tabela_item() -> None:
    tenant = TenantFactory()
    item = _cria_item(tenant)
    tabela = _cria_tabela(tenant)
    _cria_linha(tenant, tabela, item, inicio=_JAN)  # aberta
    with pytest.raises(IntegrityError):
        _cria_linha(tenant, tabela, item, inicio=_JUN)
    # Item diferente na MESMA tabela não colide.
    outro = _cria_item(tenant, codigo="P-099")
    _cria_linha(tenant, tabela, outro, inicio=_JAN)


@pytest.mark.django_db(transaction=True)
def test_linhas_adjacentes_half_open_nao_colidem() -> None:
    tenant = TenantFactory()
    item = _cria_item(tenant)
    tabela = _cria_tabela(tenant)
    _cria_linha(tenant, tabela, item, inicio=_JAN, fim=_JUN)
    _cria_linha(tenant, tabela, item, inicio=_JUN)  # [JUN, ∞) — encadeado OK
