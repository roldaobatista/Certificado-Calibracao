"""Frente `orcamentos` — Fatia 1b (T-ORC-027): drill do schema PG-real.

Cobre o COMPORTAMENTO que o drill estrutural (makemigrations) nao garante:
- RLS FORCE + 4 policies + isolamento cross-tenant nas 7 tabelas (INV-TENANT-001/002).
- WORM Padrao B PURO: UPDATE/DELETE em `orcamento_aprovacao` e `analise_critica_orcamento`
  RAISE (INV-ORC-APROVACAO-WORM / INV-ORC-ANALISE-WORM).
- WORM versao (congelamento one-shot): snapshot {}->conteudo OK; re-edicao RAISE;
  nucleo imutavel RAISE; DELETE RAISE; revogado_em permitido (D-ORC-8).
- INV-ORC-LINK-TOKEN: 1 link ativo por orcamento (partial unique).
- D-ORC-18: numero unico por tenant (mesmo numero em outro tenant OK).
- INV-ORC-EQUIP-ITEM: CHECK bifurcacao equipamento_id <-> tipo_atividade_alvo.
- INV-ORC-CONVERTIDO-TERMINAL: estado terminal nao transiciona (trigger).
- seed authz `orcamento.*` presente (matriz por perfil — D-ORC-12).

Cada RAISE/IntegrityError aborta a transacao PG -> cenarios isolados (TST-004).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError, connection
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.orcamentos import models as m

from tests.factories import TenantFactory

TABELAS_ORC = (
    "orcamento",
    "versao_orcamento",
    "item_orcamento",
    "orcamento_link_publico",
    "orcamento_aprovacao",
    "analise_critica_orcamento",
    "template_orcamento",
)

_AGORA = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_FUTURO = _AGORA + timedelta(days=30)

_PR_FAKE = {
    "item_id": "00000000-0000-0000-0000-000000000001",
    "item_versao_n": 1,
    "linha_tabela_id": "00000000-0000-0000-0000-000000000002",
    "tabela_id": "00000000-0000-0000-0000-000000000003",
    "preco": "100.00",
    "data_referencia": _AGORA.isoformat(),
    "origem_preco": "manual",
    "composicao_resolvida": [],
}


# ---------------------------------------------------------------------------
# Helpers de fixture
# ---------------------------------------------------------------------------


def _cria_orcamento(tenant, *, numero=1, estado="rascunho") -> m.Orcamento:
    with run_in_tenant_context(tenant.id):
        return m.Orcamento.objects.create(
            tenant=tenant,
            cliente_referencia_hash="v1:" + "a" * 64,
            cliente_key_id="v1",
            numero=numero,
            estado=estado,
            validade_inicio=_AGORA,
            criado_por=uuid4(),
        )


def _cria_versao(tenant, orcamento, *, numero_versao=1, snapshot=None) -> m.VersaoOrcamento:
    with run_in_tenant_context(tenant.id):
        return m.VersaoOrcamento.objects.create(
            orcamento=orcamento,
            tenant=tenant,
            numero_versao=numero_versao,
            snapshot={} if snapshot is None else snapshot,
            criada_por=uuid4(),
        )


def _cria_item(
    tenant, versao, *, sequencia=1, equipamento_id=None, tipo_alvo=""
) -> m.ItemOrcamento:
    # Mensurando obrigatorio p/ calibracao (D-ORC-5 / CHECK ck_orc_item_mensurando_calibracao).
    eh_calib = tipo_alvo == "calibracao"
    with run_in_tenant_context(tenant.id):
        return m.ItemOrcamento.objects.create(
            versao=versao,
            tenant=tenant,
            catalogo_item_id=uuid4(),
            sequencia=sequencia,
            preco_resolvido=_PR_FAKE,
            preco_final_centavos=10000,
            total_centavos=10000,
            semaforo="verde",
            descricao_snapshot="Item de teste",
            equipamento_id=equipamento_id,
            tipo_atividade_alvo=tipo_alvo,
            grandeza_solicitada="massa" if eh_calib else "",
            faixa_solicitada_min=Decimal("0") if eh_calib else None,
            faixa_solicitada_max=Decimal("500") if eh_calib else None,
            unidade_solicitada="kg" if eh_calib else "",
        )


def _cria_aprovacao(tenant, orcamento, versao) -> m.Aprovacao:
    with run_in_tenant_context(tenant.id):
        return m.Aprovacao.objects.create(
            orcamento=orcamento,
            versao=versao,
            tenant=tenant,
            aprovado_em=_AGORA,
            canal="link_publico",
            nome_aprovador_hash="x" * 64,
            email_aprovador_hash="x" * 64,
            lgpd_aceite_versao_termo="v2026-01",
            lgpd_aceite_texto_hash="x" * 64,
            ip_hash="x" * 64,
        )


def _cria_analise(tenant, orcamento, versao) -> m.AnaliseCriticaOrcamento:
    with run_in_tenant_context(tenant.id):
        return m.AnaliseCriticaOrcamento.objects.create(
            orcamento=orcamento,
            versao=versao,
            tenant=tenant,
            perfil_no_evento="A",
            veredito="aprovada",
            norma_referencia="ISO/IEC 17025:2017 cl. 7.1.1",
            itens_avaliados=[],
            snapshot_hash="x" * 64,
            avaliada_em=_AGORA,
            avaliada_por="user-1",
        )


def _cria_link(tenant, orcamento, *, token=None, revogado_em=None) -> m.LinkPublico:
    with run_in_tenant_context(tenant.id):
        return m.LinkPublico.objects.create(
            orcamento=orcamento,
            tenant=tenant,
            token=token or uuid4().hex,
            expira_em=_FUTURO,
            revogado_em=revogado_em,
        )


def _cria_template(tenant) -> m.Template:
    with run_in_tenant_context(tenant.id):
        return m.Template.objects.create(
            tenant=tenant, nome="Template teste", tipo="calibracao_balanca", criado_por=uuid4()
        )


# ---------------------------------------------------------------------------
# 1. RLS FORCE + 4 policies nas 7 tabelas
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_rls_force_e_4_policies_nas_7_tabelas() -> None:
    with connection.cursor() as cur:
        for tabela in TABELAS_ORC:
            cur.execute(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON c.relnamespace=n.oid "
                "WHERE n.nspname='public' AND c.relname=%s",
                [tabela],
            )
            row = cur.fetchone()
            assert row is not None, f"tabela {tabela} nao existe"
            enabled, forced = row
            cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [tabela])
            n_pol = cur.fetchone()[0]
            assert enabled, f"INV-TENANT-001: {tabela} sem RLS"
            assert forced, f"INV-TENANT-002: {tabela} sem FORCE"
            assert n_pol >= 4, f"{tabela} com <4 policies ({n_pol})"


# ---------------------------------------------------------------------------
# 2. RLS UNHAPPY cross-tenant nas 7 tabelas
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_rls_isola_as_7_tabelas_entre_tenants() -> None:
    """UNHAPPY cross-tenant nas 7 tabelas — INV-TENANT-001/002."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()

    orc = _cria_orcamento(tenant_a)
    versao = _cria_versao(tenant_a, orc)
    item = _cria_item(tenant_a, versao)
    link = _cria_link(tenant_a, orc)
    aprov = _cria_aprovacao(tenant_a, orc, versao)
    analise = _cria_analise(tenant_a, orc, versao)
    template = _cria_template(tenant_a)

    # tenant_b nao enxerga NADA de tenant_a.
    with run_in_tenant_context(tenant_b.id):
        assert not m.Orcamento.objects.filter(id=orc.id).exists()
        assert not m.VersaoOrcamento.objects.filter(id=versao.id).exists()
        assert not m.ItemOrcamento.objects.filter(id=item.id).exists()
        assert not m.LinkPublico.objects.filter(id=link.id).exists()
        assert not m.Aprovacao.objects.filter(id=aprov.id).exists()
        assert not m.AnaliseCriticaOrcamento.objects.filter(id=analise.id).exists()
        assert not m.Template.objects.filter(id=template.id).exists()

    # tenant_a enxerga os seus.
    with run_in_tenant_context(tenant_a.id):
        assert m.Orcamento.objects.filter(id=orc.id).exists()
        assert m.ItemOrcamento.objects.filter(id=item.id).exists()
        assert m.Aprovacao.objects.filter(id=aprov.id).exists()


# ---------------------------------------------------------------------------
# 3. WORM puro — orcamento_aprovacao
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_aprovacao_update_raise() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc)
    aprov = _cria_aprovacao(tenant, orc, versao)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        m.Aprovacao.objects.filter(id=aprov.id).update(ip_hash="y" * 64)


@pytest.mark.django_db(transaction=True)
def test_aprovacao_delete_raise() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc)
    aprov = _cria_aprovacao(tenant, orc, versao)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        m.Aprovacao.objects.filter(id=aprov.id).delete()


# ---------------------------------------------------------------------------
# 4. WORM puro — analise_critica_orcamento
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_analise_update_raise() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc)
    analise = _cria_analise(tenant, orc, versao)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        m.AnaliseCriticaOrcamento.objects.filter(id=analise.id).update(veredito="reprovada")


@pytest.mark.django_db(transaction=True)
def test_analise_delete_raise() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc)
    analise = _cria_analise(tenant, orc, versao)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        m.AnaliseCriticaOrcamento.objects.filter(id=analise.id).delete()


# ---------------------------------------------------------------------------
# 5. WORM versao — congelamento one-shot
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_versao_snapshot_one_shot_fill() -> None:
    """snapshot {} -> conteudo OK (congela); re-edicao do congelado RAISE."""
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc, snapshot={})
    # Congelar (one-shot): permitido.
    with run_in_tenant_context(tenant.id):
        m.VersaoOrcamento.objects.filter(id=versao.id).update(snapshot={"itens": [1, 2]})
    # Re-editar o snapshot congelado: RAISE.
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        m.VersaoOrcamento.objects.filter(id=versao.id).update(snapshot={"itens": [9]})


@pytest.mark.django_db(transaction=True)
def test_versao_nucleo_imutavel_raise() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc, numero_versao=1)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        m.VersaoOrcamento.objects.filter(id=versao.id).update(numero_versao=99)


@pytest.mark.django_db(transaction=True)
def test_versao_delete_raise() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        m.VersaoOrcamento.objects.filter(id=versao.id).delete()


@pytest.mark.django_db(transaction=True)
def test_versao_revogacao_permitida() -> None:
    """revogado_em pode ser setado mesmo na versao congelada (soft-revoke — D-ORC-8)."""
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc, snapshot={"itens": [1]})
    with run_in_tenant_context(tenant.id):
        m.VersaoOrcamento.objects.filter(id=versao.id).update(
            revogado_em=_AGORA, motivo_revogacao="substituida na renegociacao"
        )
        assert m.VersaoOrcamento.objects.get(id=versao.id).revogado_em is not None


# ---------------------------------------------------------------------------
# 6. Partial unique — 1 link ativo por orcamento
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_link_unico_ativo_por_orcamento() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    _cria_link(tenant, orc)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_link(tenant, orc)  # 2o link ativo no mesmo orcamento


@pytest.mark.django_db(transaction=True)
def test_link_segundo_apos_revogar_primeiro_ok() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    link1 = _cria_link(tenant, orc)
    with run_in_tenant_context(tenant.id):
        m.LinkPublico.objects.filter(id=link1.id).update(revogado_em=_AGORA)
    link2 = _cria_link(tenant, orc)  # agora permitido
    with run_in_tenant_context(tenant.id):
        assert m.LinkPublico.objects.filter(id=link2.id, revogado_em__isnull=True).exists()


# ---------------------------------------------------------------------------
# 7. Unique numero por tenant
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_numero_unico_por_tenant() -> None:
    tenant = TenantFactory()
    _cria_orcamento(tenant, numero=7)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_orcamento(tenant, numero=7)


@pytest.mark.django_db(transaction=True)
def test_mesmo_numero_em_tenants_diferentes_ok() -> None:
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    _cria_orcamento(tenant_a, numero=7)
    orc_b = _cria_orcamento(tenant_b, numero=7)  # mesmo numero, outro tenant — OK
    with run_in_tenant_context(tenant_b.id):
        assert m.Orcamento.objects.filter(id=orc_b.id).exists()


# ---------------------------------------------------------------------------
# 8. CHECK bifurcacao item — INV-ORC-EQUIP-ITEM
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_item_tecnico_sem_tipo_alvo_raise() -> None:
    """equipamento_id preenchido + tipo_atividade_alvo='' -> CHECK RAISE."""
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_item(tenant, versao, equipamento_id=uuid4(), tipo_alvo="")


@pytest.mark.django_db(transaction=True)
def test_item_comercial_com_tipo_alvo_raise() -> None:
    """equipamento_id=None + tipo_atividade_alvo!='' -> CHECK RAISE."""
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_item(tenant, versao, equipamento_id=None, tipo_alvo="calibracao")


@pytest.mark.django_db(transaction=True)
def test_item_tecnico_e_comercial_validos_ok() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant)
    versao = _cria_versao(tenant, orc)
    tecnico = _cria_item(
        tenant, versao, sequencia=1, equipamento_id=uuid4(), tipo_alvo="calibracao"
    )
    comercial = _cria_item(tenant, versao, sequencia=2, equipamento_id=None, tipo_alvo="")
    with run_in_tenant_context(tenant.id):
        assert m.ItemOrcamento.objects.filter(id=tecnico.id).exists()
        assert m.ItemOrcamento.objects.filter(id=comercial.id).exists()


# ---------------------------------------------------------------------------
# 9. Trigger estado terminal — INV-ORC-CONVERTIDO-TERMINAL
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_estado_terminal_nao_transiciona() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant, estado="convertido")
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        m.Orcamento.objects.filter(id=orc.id).update(estado="rascunho")


@pytest.mark.django_db(transaction=True)
def test_estado_nao_terminal_transiciona_ok() -> None:
    tenant = TenantFactory()
    orc = _cria_orcamento(tenant, estado="rascunho")
    with run_in_tenant_context(tenant.id):
        m.Orcamento.objects.filter(id=orc.id).update(estado="enviado")
        assert m.Orcamento.objects.get(id=orc.id).estado == "enviado"


# ---------------------------------------------------------------------------
# 10. Seed authz orcamento.* presente (D-ORC-12)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_seed_authz_orcamento_presente() -> None:
    """admin_tenant tem orcamento.criar; metrologista_bancada so orcamento.ver.

    transaction=True: a fixture `_restaura_seeds_apos_truncate` re-aplica os seeds
    (incl. orcamentos/0006) no setup quando `authz_perfil_acao` foi truncado por um
    TransactionTestCase anterior — senao o teste veria a tabela vazia.
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM authz_perfil_acao pa "
            "JOIN authz_perfil p ON pa.perfil_id = p.id "
            "WHERE p.codigo = 'admin_tenant' AND pa.acao = 'orcamento.criar';"
        )
        assert cur.fetchone()[0] == 1, "admin_tenant deveria ter orcamento.criar"

        cur.execute(
            "SELECT COUNT(*) FROM authz_perfil_acao pa "
            "JOIN authz_perfil p ON pa.perfil_id = p.id "
            "WHERE p.codigo = 'metrologista_bancada' AND pa.acao = 'orcamento.ver';"
        )
        assert cur.fetchone()[0] == 1, "metrologista_bancada deveria ter orcamento.ver"

        cur.execute(
            "SELECT COUNT(*) FROM authz_perfil_acao pa "
            "JOIN authz_perfil p ON pa.perfil_id = p.id "
            "WHERE p.codigo = 'metrologista_bancada' AND pa.acao = 'orcamento.criar';"
        )
        assert cur.fetchone()[0] == 0, "metrologista_bancada NAO deveria ter orcamento.criar"
