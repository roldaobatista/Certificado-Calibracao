"""Frente `precificacao` — Fatia 1b (T-PRC-028): schema PG-real.

Cobre o COMPORTAMENTO que o drill estrutural não garante:
- RLS FORCE + policies + isolamento cross-tenant nas 7 tabelas (INV-TENANT-001/002).
- INV-PRC-REGRA-IMUTAVEL: UPDATE de campo probatório RAISE; DELETE físico RAISE;
  vigencia_fim/revogado_em one-shot (trigger 0003).
- INV-PRC-APROVACAO-ONE-SHOT: 2ª decisão de pedido RAISE; campo probatório pós-
  decisão RAISE (trigger 0003).
- INV-PRC-APROVACAO-INDEPENDENTE: CHECK decisor != solicitante RAISE.
- INV-PRC-REGRA-SEM-SOBREPOSICAO: exclusion btree_gist (overlap RAISE; revogada +
  substituta mesma janela OK).
- seed authz precificacao.* presente (4 ações).

Cada RAISE aborta a transação PG → cenários isolados (TST-004).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.precificacao.models import (
    FaixaAprovacaoDesconto,
    JustificativaDecisaoDesconto,
    ParametrosPrecificacaoTenant,
    PedidoAprovacaoDesconto,
    PerfilComposicaoPreco,
    RegraFormacaoPreco,
    VinculoTabelaPrecoCliente,
)

from tests.factories import TenantFactory

TABELAS_PRC = (
    "regra_formacao_preco",
    "perfil_composicao_preco",
    "faixa_aprovacao_desconto",
    "pedido_aprovacao_desconto",
    "justificativa_decisao_desconto",
    "vinculo_tabela_preco_cliente",
    "parametros_precificacao_tenant",
)

_JAN = datetime(2026, 1, 1, tzinfo=UTC)
_JUN = datetime(2026, 6, 1, tzinfo=UTC)
_DEZ = datetime(2026, 12, 31, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Helpers para criar fixtures mínimas
# ---------------------------------------------------------------------------

def _item_id(tenant) -> UUID:
    """Cria ItemCatalogo e retorna ID (reusa PPS já migrada)."""
    from src.infrastructure.produtos_pecas_servicos.models import ItemCatalogo
    with run_in_tenant_context(tenant.id):
        item = ItemCatalogo.objects.create(
            tenant=tenant,
            codigo_interno=f"ITEM-PRC-{uuid4().hex[:8]}",
            tipo="servico",
            controla_estoque=False,
        )
    return item.id


def _cria_regra(
    tenant,
    item_id=None,
    *,
    versao_n=1,
    modo="preco_fixo",
    inicio=_JAN,
    fim=None,
) -> RegraFormacaoPreco:
    with run_in_tenant_context(tenant.id):
        iid = item_id or _item_id(tenant)
        return RegraFormacaoPreco.objects.create(
            tenant=tenant,
            item_id=iid,
            modo=modo,
            versao_n=versao_n,
            preco_fixo=Decimal("100.00"),
            vigencia_inicio=inicio,
            vigencia_fim=fim,
            criado_por=uuid4(),
        )


def _cria_pedido(
    tenant,
    *,
    estado="solicitado",
    solicitante=None,
    decisor=None,
) -> PedidoAprovacaoDesconto:
    sol = solicitante or uuid4()
    with run_in_tenant_context(tenant.id):
        return PedidoAprovacaoDesconto.objects.create(
            tenant=tenant,
            contexto_tipo="avulso",
            pct_solicitado=Decimal("15.00"),
            cortesia=False,
            alcada_exigida="gerente",
            fingerprint_calculo="abc123",
            estado=estado,
            solicitante_id=sol,
            decisor_id=decisor,
            snapshot_probatorio='{"eco": "teste"}',
        )


# ---------------------------------------------------------------------------
# 1. RLS: FORCE + 4 policies nas 7 tabelas
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_rls_force_e_4_policies_nas_7_tabelas_prc() -> None:
    with connection.cursor() as cur:
        for tabela in TABELAS_PRC:
            cur.execute(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON c.relnamespace=n.oid "
                "WHERE n.nspname='public' AND c.relname=%s",
                [tabela],
            )
            row = cur.fetchone()
            assert row is not None, f"tabela {tabela} não existe"
            enabled, forced = row
            cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [tabela])
            n_pol = cur.fetchone()[0]
            assert enabled, f"INV-TENANT-001: {tabela} sem RLS"
            assert forced, f"INV-TENANT-002: {tabela} sem FORCE"
            assert n_pol >= 4, f"{tabela} com <4 policies ({n_pol})"


# ---------------------------------------------------------------------------
# 2. RLS UNHAPPY cross-tenant (×7 tabelas — lição B1 da frente #1)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_rls_isola_as_7_tabelas_entre_tenants() -> None:
    """UNHAPPY cross-tenant nas 7 tabelas — INV-TENANT-001/002."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()

    iid = _item_id(tenant_a)

    with run_in_tenant_context(tenant_a.id):
        regra = RegraFormacaoPreco.objects.create(
            tenant=tenant_a, item_id=iid, modo="preco_fixo", versao_n=1,
            preco_fixo=Decimal("100.00"), vigencia_inicio=_JAN, criado_por=uuid4(),
        )
        perfil = PerfilComposicaoPreco.objects.create(
            tenant=tenant_a, item_servico_id=iid, componentes_esperados=[],
            criado_por=uuid4(),
        )
        faixa = FaixaAprovacaoDesconto.objects.create(
            tenant=tenant_a, pct_de=Decimal("0.00"), pct_ate=Decimal("10.00"),
            alcada="livre", versao_n=1, hash_conjunto="h1", criado_por=uuid4(),
        )
        pedido = PedidoAprovacaoDesconto.objects.create(
            tenant=tenant_a, contexto_tipo="avulso",
            pct_solicitado=Decimal("5.00"), cortesia=False,
            alcada_exigida="livre", fingerprint_calculo="fp1",
            estado="solicitado", solicitante_id=uuid4(),
            snapshot_probatorio='{"test": 1}',
        )
        just = JustificativaDecisaoDesconto.objects.create(
            tenant=tenant_a, pedido=pedido, texto="Justificativa de teste.",
        )
        vinculo = VinculoTabelaPrecoCliente.objects.create(
            tenant=tenant_a, tabela_id=uuid4(), cliente_id=uuid4(),
            vigencia_inicio=_JAN, criado_por=uuid4(),
        )
        param = ParametrosPrecificacaoTenant.objects.create(
            tenant=tenant_a, versao_n=1, custo_km=Decimal("1.5000"),
            taxa_parcelamento_mensal=Decimal("2.00"),
            pct_comissao_prevista=Decimal("5.00"),
            margem_alvo_default=Decimal("30.00"),
            margem_piso_default=Decimal("10.00"),
            criado_por=uuid4(),
        )

    # tenant_b não enxerga nada de tenant_a
    with run_in_tenant_context(tenant_b.id):
        assert not RegraFormacaoPreco.objects.filter(id=regra.id).exists()
        assert not PerfilComposicaoPreco.objects.filter(id=perfil.id).exists()
        assert not FaixaAprovacaoDesconto.objects.filter(id=faixa.id).exists()
        assert not PedidoAprovacaoDesconto.objects.filter(id=pedido.id).exists()
        assert not JustificativaDecisaoDesconto.objects.filter(id=just.id).exists()
        assert not VinculoTabelaPrecoCliente.objects.filter(id=vinculo.id).exists()
        assert not ParametrosPrecificacaoTenant.objects.filter(id=param.id).exists()

    # tenant_a enxerga seus próprios dados
    with run_in_tenant_context(tenant_a.id):
        assert RegraFormacaoPreco.objects.filter(id=regra.id).exists()
        assert ParametrosPrecificacaoTenant.objects.filter(id=param.id).exists()


# ---------------------------------------------------------------------------
# 3. INV-PRC-REGRA-IMUTAVEL — UPDATE direto em campo probatório RAISE
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_update_direto_campo_probatorio_regra_raise() -> None:
    """UPDATE direto no modo (campo probatório) da regra DEVE levantar DatabaseError."""
    tenant = TenantFactory()
    regra = _cria_regra(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegraFormacaoPreco.objects.filter(id=regra.id).update(modo="margem_alvo")


@pytest.mark.django_db(transaction=True)
def test_update_direto_preco_fixo_regra_raise() -> None:
    """UPDATE direto no preco_fixo (campo probatório) DEVE levantar DatabaseError."""
    tenant = TenantFactory()
    regra = _cria_regra(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegraFormacaoPreco.objects.filter(id=regra.id).update(preco_fixo=Decimal("999.99"))


@pytest.mark.django_db(transaction=True)
def test_delete_direto_regra_raise() -> None:
    """DELETE físico de regra DEVE levantar DatabaseError (retenção 5a)."""
    tenant = TenantFactory()
    regra = _cria_regra(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegraFormacaoPreco.objects.filter(id=regra.id).delete()


@pytest.mark.django_db(transaction=True)
def test_vigencia_fim_one_shot_regra() -> None:
    """vigencia_fim one-shot: NULL→data OK; re-escrita RAISE."""
    tenant = TenantFactory()
    regra = _cria_regra(tenant, inicio=_JAN, fim=None)
    # Primeiro encerramento: OK
    with run_in_tenant_context(tenant.id):
        RegraFormacaoPreco.objects.filter(id=regra.id).update(vigencia_fim=_JUN)
    # Segundo encerramento (re-escrita): RAISE
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegraFormacaoPreco.objects.filter(id=regra.id).update(vigencia_fim=_DEZ)


@pytest.mark.django_db(transaction=True)
def test_revogacao_one_shot_regra() -> None:
    """revogado_em one-shot: NULL→data OK; mutação posterior RAISE."""
    tenant = TenantFactory()
    regra = _cria_regra(tenant)
    with run_in_tenant_context(tenant.id):
        RegraFormacaoPreco.objects.filter(id=regra.id).update(
            revogado_em=timezone.now(), motivo_revogacao="Regra errada (10+ chars)."
        )
    # Tenta mudar revogado_em novamente
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegraFormacaoPreco.objects.filter(id=regra.id).update(revogado_em=timezone.now())


# ---------------------------------------------------------------------------
# 4. INV-PRC-APROVACAO-ONE-SHOT — 2ª decisão RAISE
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_segunda_decisao_pedido_raise() -> None:
    """2ª tentativa de decidir pedido já decidido DEVE levantar DatabaseError."""
    tenant = TenantFactory()
    decisor = uuid4()
    sol = uuid4()
    with run_in_tenant_context(tenant.id):
        pedido = PedidoAprovacaoDesconto.objects.create(
            tenant=tenant, contexto_tipo="avulso",
            pct_solicitado=Decimal("15.00"), cortesia=False,
            alcada_exigida="gerente", fingerprint_calculo="fp123",
            estado="solicitado", solicitante_id=sol,
            snapshot_probatorio='{"test": 1}',
        )
    # 1ª decisão: OK
    with run_in_tenant_context(tenant.id):
        PedidoAprovacaoDesconto.objects.filter(id=pedido.id).update(
            estado="aprovado", decisor_id=decisor, decidido_em=timezone.now(),
            justificativa_hash="hash_aprovacao",
        )
    # 2ª decisão: RAISE (estado já terminal)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        PedidoAprovacaoDesconto.objects.filter(id=pedido.id).update(
            estado="negado", decisor_id=uuid4(), decidido_em=timezone.now(),
        )


@pytest.mark.django_db(transaction=True)
def test_campo_probatorio_pedido_pos_decisao_raise() -> None:
    """Campo probatório (pct_solicitado) de pedido pós-decisão RAISE."""
    tenant = TenantFactory()
    sol = uuid4()
    dec = uuid4()
    with run_in_tenant_context(tenant.id):
        pedido = PedidoAprovacaoDesconto.objects.create(
            tenant=tenant, contexto_tipo="avulso",
            pct_solicitado=Decimal("15.00"), cortesia=False,
            alcada_exigida="gerente", fingerprint_calculo="fp456",
            estado="solicitado", solicitante_id=sol,
            snapshot_probatorio='{"test": 2}',
        )
    with run_in_tenant_context(tenant.id):
        PedidoAprovacaoDesconto.objects.filter(id=pedido.id).update(
            estado="aprovado", decisor_id=dec, decidido_em=timezone.now(),
            justificativa_hash="hash_ok",
        )
    # Tenta mutar pct_solicitado (campo probatório) RAISE
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        PedidoAprovacaoDesconto.objects.filter(id=pedido.id).update(
            pct_solicitado=Decimal("50.00")
        )


# ---------------------------------------------------------------------------
# 5. INV-PRC-APROVACAO-INDEPENDENTE — CHECK decisor != solicitante RAISE
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_check_decisor_igual_solicitante_raise() -> None:
    """decisor_id == solicitante_id DEVE violar CHECK (IntegrityError)."""
    tenant = TenantFactory()
    mesmo_user = uuid4()
    with run_in_tenant_context(tenant.id):
        # Cria pedido com solicitante
        pedido = PedidoAprovacaoDesconto.objects.create(
            tenant=tenant, contexto_tipo="avulso",
            pct_solicitado=Decimal("20.00"), cortesia=False,
            alcada_exigida="gerente", fingerprint_calculo="fp789",
            estado="solicitado", solicitante_id=mesmo_user,
            snapshot_probatorio='{"test": 3}',
        )
    # Tenta decidir com o mesmo user (decisor == solicitante) — CHECK viola
    with run_in_tenant_context(tenant.id), pytest.raises((IntegrityError, DatabaseError)):
        PedidoAprovacaoDesconto.objects.filter(id=pedido.id).update(
            estado="aprovado",
            decisor_id=mesmo_user,  # mesmo que solicitante_id
            decidido_em=timezone.now(),
            justificativa_hash="hash_test",
        )


# ---------------------------------------------------------------------------
# 6. INV-PRC-REGRA-SEM-SOBREPOSICAO — exclusion btree_gist
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_exclusion_sobreposicao_vigencia_raise() -> None:
    """Duas regras não-revogadas para o mesmo item sobrepostas RAISE."""
    tenant = TenantFactory()
    iid = _item_id(tenant)
    _cria_regra(tenant, iid, versao_n=1, inicio=_JAN, fim=_DEZ)
    # Vigência sobreposta sem revogação = exclusion violation
    with run_in_tenant_context(tenant.id), pytest.raises((IntegrityError, DatabaseError)):
        RegraFormacaoPreco.objects.create(
            tenant=tenant, item_id=iid, modo="preco_fixo", versao_n=2,
            preco_fixo=Decimal("200.00"), vigencia_inicio=_JUN, vigencia_fim=None,
            criado_por=uuid4(),
        )


@pytest.mark.django_db(transaction=True)
def test_exclusion_revogada_mais_substituta_mesma_janela_ok() -> None:
    """Regra revogada + substituta na MESMA janela NÃO viola exclusion (sai da exclusion).

    Lição M2 da frente #2: revogada sai da exclusion (WHERE revogado_em IS NULL).
    """
    tenant = TenantFactory()
    iid = _item_id(tenant)
    regra_errada = _cria_regra(tenant, iid, versao_n=1, inicio=_JAN, fim=_DEZ)
    # Revoga a regra errada (sai da exclusion)
    with run_in_tenant_context(tenant.id):
        RegraFormacaoPreco.objects.filter(id=regra_errada.id).update(
            revogado_em=timezone.now(), motivo_revogacao="Regra errada criada em teste."
        )
    # Corrigida pode ter a mesma janela sem violar exclusion
    with run_in_tenant_context(tenant.id):
        regra_correta = RegraFormacaoPreco.objects.create(
            tenant=tenant, item_id=iid, modo="preco_fixo", versao_n=2,
            preco_fixo=Decimal("150.00"), vigencia_inicio=_JAN, vigencia_fim=_DEZ,
            criado_por=uuid4(),
        )
    with run_in_tenant_context(tenant.id):
        assert RegraFormacaoPreco.objects.filter(id=regra_correta.id).exists()


# ---------------------------------------------------------------------------
# 7. Seed authz precificacao.* presente (4 ações)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_seed_authz_precificacao_presente() -> None:
    """Seed authz deve ter as 4 ações de precificacao.* (T-PRC-025).

    transaction=True para que a fixture _restaura_seeds_apos_truncate
    reaplique a seed após o TRUNCATE transacional (molde PPS/CFG).
    """
    ACOES = [
        "precificacao.configurar",
        "precificacao.calcular",
        "precificacao.ver_margem",
        "precificacao.aprovar_desconto",
    ]
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(DISTINCT acao) FROM authz_perfil_acao WHERE acao = ANY(%s);",
            [ACOES],
        )
        n = cur.fetchone()[0]
    assert n == 4, f"Esperado 4 ações authz precificacao.*, encontrado {n}"


# ---------------------------------------------------------------------------
# 8. Verificação: papel aprovador tem ver_margem (coerência D-PRC-4)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_papel_aprovador_tem_ver_margem() -> None:
    """signatario (papel aprovador) DEVE ter precificacao.ver_margem (D-PRC-4).

    transaction=True para que a fixture _restaura_seeds_apos_truncate
    reaplique a seed após o TRUNCATE transacional.
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM authz_perfil_acao pa "
            "JOIN authz_perfil p ON pa.perfil_id = p.id "
            "WHERE p.codigo = 'signatario' AND pa.acao = 'precificacao.ver_margem' "
            "AND p.tenant_id IS NULL;",
        )
        n = cur.fetchone()[0]
    assert n >= 1, "signatario (papel aprovador) deve ter precificacao.ver_margem (D-PRC-4)"
