"""T-CLI-115 + T-CLI-119 (US-CLI-006) — revogação consentimento +
evento incidente PII.

Cobertura T-CLI-115 (AC-CLI-006-2 — LGPD art. 8º §5º):
1. test_revogar_consentimento_seta_timestamp
2. test_revogar_consentimento_2x_levanta_clienteja_revogou
3. test_revogar_consentimento_publica_evento_cadeia_F_A
4. test_revogar_consentimento_publica_outbox
5. test_base_legal_aplicavel_pos_revogacao_consentimento_marketing_recusado
6. test_base_legal_aplicavel_pos_revogacao_emissao_nf_subsiste

Cobertura T-CLI-119 (AC-CLI-006-6 — Res. ANPD 15/2024):
7. test_emitir_incidente_com_cliente_ids_calcula_qt
8. test_emitir_incidente_com_escopo_base_inteira_aceita_declarada
9. test_emitir_incidente_escopo_invalido_rejeita
10. test_emitir_incidente_default_conservador_registro_unico
11. test_emitir_incidente_publica_acao_canonica
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import connection
from src.infrastructure.audit.politicas_lgpd import (
    base_legal_aplicavel_pos_revogacao,
)
from src.infrastructure.clientes.direitos_titular import (
    ClienteJaRevogou,
    emitir_incidente_pii,
    revogar_consentimento,
)
from src.infrastructure.clientes.models import Cliente
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)

from tests.factories import TenantFactory


def _criar_cliente(tenant) -> Cliente:
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa="PF",
        documento="11144477735",
        nome="Foo Bar",
        aceite_lgpd_em="2026-05-20T10:00:00Z",
        aceite_lgpd_versao="v1",
        aceite_lgpd_origem="CADASTRO_DIRETO",
        aceite_lgpd_base_legal="CONSENTIMENTO",
    )


# =============================================================
# T-CLI-115 — revogação consentimento
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_revogar_consentimento_seta_timestamp():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant)
        assert cli.consentimento_revogado_em is None
        revogar_consentimento(cliente=cli, tenant_id=tenant.id, usuario_id=None)
        cli.refresh_from_db()
    assert cli.consentimento_revogado_em is not None


@pytest.mark.django_db(transaction=True)
def test_revogar_consentimento_2x_levanta_clienteja_revogou():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant)
        revogar_consentimento(cliente=cli, tenant_id=tenant.id, usuario_id=None)
        with pytest.raises(ClienteJaRevogou, match="já revogou"):
            revogar_consentimento(cliente=cli, tenant_id=tenant.id, usuario_id=None)


@pytest.mark.django_db(transaction=True)
def test_revogar_consentimento_publica_evento_cadeia_F_A():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant)
        revogar_consentimento(cliente=cli, tenant_id=tenant.id, usuario_id=None)
        # SELECT na cadeia F-A precisa do contexto do tenant
        # (policy SELECT: tenant_id ∈ app.tenant_ids; modo_sistema só vê NULL).
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM auditoria "
                "WHERE action = 'cliente.consentimento_revogado' "
                "AND payload_jsonb->>'cliente_id' = %s",
                [str(cli.id)],
            )
            assert cur.fetchone()[0] == 1


@pytest.mark.django_db(transaction=True)
def test_revogar_consentimento_publica_outbox():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        cli = _criar_cliente(tenant)
        revogar_consentimento(cliente=cli, tenant_id=tenant.id, usuario_id=None)
    # bus_outbox: modo_sistema vê TUDO (divergência justificada)
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM bus_outbox "
                "WHERE acao = 'cliente.consentimento_revogado' "
                "AND tenant_id = %s",
                [str(tenant.id)],
            )
            assert cur.fetchone()[0] == 1


# =============================================================
# Mapa finalidade × base legal (BLOQ-A2 advogado)
# =============================================================


def test_base_legal_aplicavel_pos_revogacao_consentimento_marketing_recusado():
    """Pos revogacao: comunicacao_marketing depende SO de CONSENTIMENTO →
    nao tem base legal aplicavel."""
    assert base_legal_aplicavel_pos_revogacao("comunicacao_marketing", {"CONSENTIMENTO"}) is False


def test_base_legal_aplicavel_pos_revogacao_emissao_nf_subsiste():
    """Emissao NF aceita OBRIG_LEGAL → subsiste apos revogacao."""
    assert (
        base_legal_aplicavel_pos_revogacao("emissao_nf", {"CONSENTIMENTO", "OBRIG_LEGAL"}) is True
    )


# =============================================================
# T-CLI-119 — evento incidente PII
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_emitir_incidente_com_cliente_ids_calcula_qt():
    tenant = TenantFactory()
    cids = [uuid4(), uuid4(), uuid4()]
    with run_in_tenant_context(tenant.id):
        resultado = emitir_incidente_pii(
            tenant_id=tenant.id,
            descricao_curta="acesso indevido",
            categoria_pii_afetada="pii_identificadora",
            cliente_ids=cids,
        )
    assert resultado["qt_titulares_estimada"] == 3
    assert resultado["escopo"] == "subconjunto_filtrado"


@pytest.mark.django_db(transaction=True)
def test_emitir_incidente_com_escopo_base_inteira_aceita_declarada():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        resultado = emitir_incidente_pii(
            tenant_id=tenant.id,
            descricao_curta="dump indevido",
            categoria_pii_afetada="pii_identificadora",
            escopo="base_inteira",
            qt_titulares_declarada=1500,
        )
    assert resultado["escopo"] == "base_inteira"
    assert resultado["qt_titulares_estimada"] == 1500


@pytest.mark.django_db(transaction=True)
def test_emitir_incidente_escopo_invalido_rejeita():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        with pytest.raises(ValueError, match="escopo invalido"):
            emitir_incidente_pii(
                tenant_id=tenant.id,
                descricao_curta="x",
                categoria_pii_afetada="pii_identificadora",
                escopo="universo_inteiro_ilimitado",
            )


@pytest.mark.django_db(transaction=True)
def test_emitir_incidente_default_conservador_registro_unico():
    """Default BLOQ-A5: sem cliente_ids E sem escopo → registro_unico qt=1."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        resultado = emitir_incidente_pii(
            tenant_id=tenant.id,
            descricao_curta="x",
            categoria_pii_afetada="pii_identificadora",
        )
    assert resultado["escopo"] == "registro_unico"
    assert resultado["qt_titulares_estimada"] == 1


@pytest.mark.django_db(transaction=True)
def test_emitir_incidente_publica_acao_canonica():
    """Acao deve estar em ACOES_CANONICAS (publicar_evento valida).

    Evento publicado com tenant_id=tenant — visível no contexto do tenant.
    """
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        emitir_incidente_pii(
            tenant_id=tenant.id,
            descricao_curta="x",
            categoria_pii_afetada="pii_identificadora",
        )
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM auditoria " "WHERE action = 'cliente.pii.incidente_detectado'"
            )
            assert cur.fetchone()[0] >= 1
