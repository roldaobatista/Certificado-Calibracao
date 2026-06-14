"""DRILL da Fatia 1c — os-multi-equipamento (ADR-0082 / D-OSME-2 + D-OSME-3).

Cobre:
(a) OS com equipamento=NULL persiste OK (D-OSME-2).
(b) ItemComercialOS persiste via repositorio + listar_itens_comerciais_por_os retorna.
(c) RLS cross-tenant: tenant B nao enxerga ItemComercialOS do tenant A (UNHAPPY).

Cuidados do projeto:
- Usa TenantFactory para criar tenant.
- Usa run_in_tenant_context para propagar RLS + pii_hash_key_ativa.
- NUNCA dropar test_afere nem usar --create-db.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from django.db import connection
from src.domain.operacao.os.entities import ItemComercialOSSnapshot
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import ItemComercialOS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory


def _next_seq() -> int:
    """Chama nextval da sequence global de numero_os."""
    with connection.cursor() as cur:
        cur.execute("SELECT nextval('os_numero_seq_global')")
        return int(cur.fetchone()[0])


def _criar_equip_cliente_e_os(tenant, *, equipamento_id=None):
    """Cria equipamento + cliente + OS para o tenant via SQL.

    Deve ser chamada DENTRO de run_in_tenant_context. Retorna (equip_id, os_id).
    Quando equipamento_id=None, a OS e criada com equipamento NULL (multi-equip).
    """
    equip_id = equipamento_id or uuid.uuid4()
    cli_id = uuid.uuid4()
    os_id = uuid.uuid4()
    numero = _next_seq()
    tag = f"F1C-{uuid.uuid4().hex[:8]}"
    doc = f"{uuid.uuid4().int % 99999999999999:014d}"
    nome_cli = f"CliF1C-{tag}"

    with connection.cursor() as cur:
        # Equipamento — sempre cria (mesmo quando OS fica com NULL, um equip existe no tenant).
        cur.execute(
            """
            INSERT INTO equipamentos (
                id, tenant_id, tag, numero_serie, fabricante, modelo,
                faixa, classe, localizacao_fisica,
                perfil_tenant_snapshot, snapshot_schema_version,
                status, criado_em, atualizado_em
            ) VALUES (
                %s, %s, %s, %s, 'FabF1C', 'ModF1C',
                '', '', '',
                %s::jsonb, 'v1',
                'ativo', now(), now()
            )
            """,
            [str(equip_id), str(tenant.id), tag, tag, '{"perfil": "D"}'],
        )

        # Cliente.
        cur.execute(
            """
            INSERT INTO clientes (
                id, tenant_id, tipo_pessoa, documento, nome, nome_fantasia,
                email, telefone,
                aceite_lgpd_dispensa_motivo,
                aceite_lgpd_ip_hash, aceite_lgpd_origem, aceite_lgpd_versao,
                aceite_lgpd_base_legal, aceite_lgpd_evidencia_externa,
                aceite_lgpd_pendente, cpf_responsavel_legal,
                cliente_canonico_id, observacao, deletado_motivo_categoria,
                criado_em, atualizado_em
            ) VALUES (
                %s, %s, 'PJ', %s, %s, %s,
                '', '',
                'pj_sem_pf_associada',
                '', '', '',
                '', '',
                false, '',
                %s, '', '',
                now(), now()
            )
            """,
            [str(cli_id), str(tenant.id), doc, nome_cli, nome_cli, str(cli_id)],
        )

        # TipoAtividadeConfig seed.
        cur.execute(
            """
            INSERT INTO tipo_atividade_config (
                tenant_id, tipo, requer_competencia_rt,
                tipo_bloqueia_concorrencia, executa_em_campo,
                criado_em, atualizado_em
            ) VALUES (%s, 'calibracao', false, true, false, now(), now())
            ON CONFLICT (tenant_id, tipo) WHERE deletado_em IS NULL DO NOTHING
            """,
            [str(tenant.id)],
        )

        # OS — equipamento_id pode ser NULL (D-OSME-2) ou um UUID.
        equip_col = str(equip_id) if equipamento_id is not None else None
        cur.execute(
            """
            INSERT INTO ordens_servico (
                id, tenant_id, numero_os, cliente_id,
                cliente_referencia_hash, cliente_key_id,
                equipamento_id, estado, tipo_predominante,
                nao_conformidade_global, valor_total, valor_total_atualizado,
                analise_critica_snapshot_hash,
                regra_decisao_acordada, criada_em, atualizada_em
            ) VALUES (
                %s, %s, %s, %s,
                %s, 'kms-f1c',
                %s, 'rascunho', '',
                false, 0, 0,
                %s,
                'default', now(), now()
            )
            """,
            [
                str(os_id), str(tenant.id), numero, str(cli_id),
                "a" * 64,
                equip_col,
                "b" * 64,
            ],
        )

    return equip_id, os_id


# =============================================================
# Teste (a) — OS com equipamento=NULL persiste OK (D-OSME-2)
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_osme_f1c_a_os_equipamento_null_persiste():
    """(a) OS com equipamento=NULL (multi-equip) persiste e IS NULL no banco."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        equip_id, os_id = _criar_equip_cliente_e_os(tenant, equipamento_id=None)

        with connection.cursor() as cur:
            cur.execute(
                "SELECT equipamento_id FROM ordens_servico WHERE id = %s",
                [str(os_id)],
            )
            row = cur.fetchone()

    assert row is not None, "OS deve existir no banco"
    assert row[0] is None, (
        f"OS multi-equipamento deve ter equipamento_id=NULL, got {row[0]}"
    )


# =============================================================
# Teste (b) — ItemComercialOS persiste via repo + listagem retorna
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_osme_f1c_b_item_comercial_persiste_e_lista():
    """(b) ItemComercialOS persiste via salvar_item_comercial e listagem retorna."""
    tenant = TenantFactory()
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id):
        _equip_id, os_id = _criar_equip_cliente_e_os(tenant, equipamento_id=None)

        item_id = uuid.uuid4()
        snapshot = ItemComercialOSSnapshot(
            id=item_id,
            tenant_id=tenant.id,
            os_id=os_id,
            tipo=TipoItemComercial.DESLOCAMENTO,
            descricao_publica="Deslocamento 50 km",
            valor=Decimal("75.00"),
            quantidade=1,
            origem_item_id=None,
        )
        salvo = repo.salvar_item_comercial(snapshot)

        assert salvo.id == item_id
        assert salvo.tipo == TipoItemComercial.DESLOCAMENTO
        assert salvo.valor == Decimal("75.00")

        itens = repo.listar_itens_comerciais_por_os(os_id)

    assert len(itens) == 1, f"Esperado 1 item, got {len(itens)}"
    assert itens[0].id == item_id
    assert itens[0].descricao_publica == "Deslocamento 50 km"

    # INV-OSME-ITEMCOM-001: confirma que o model NAO tem equipamento_id nem
    # tipo_bloqueia_concorrencia.
    assert not hasattr(ItemComercialOS, "equipamento_id"), (
        "INV-OSME-ITEMCOM-001: ItemComercialOS NAO deve ter equipamento_id"
    )
    assert not hasattr(ItemComercialOS, "tipo_bloqueia_concorrencia"), (
        "INV-OSME-ITEMCOM-001: ItemComercialOS NAO deve ter tipo_bloqueia_concorrencia"
    )


# =============================================================
# Teste (c) — RLS cross-tenant UNHAPPY: tenant B nao ve item do tenant A
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_osme_f1c_c_rls_cross_tenant_item_comercial():
    """(c) UNHAPPY: tenant B nao enxerga ItemComercialOS do tenant A (RLS policy).

    Cria item no contexto do tenant A, depois verifica via SQL raw com
    app.tenant_ids do tenant B que o SELECT retorna 0 linhas.
    """
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    repo = DjangoOSRepository()

    item_id = uuid.uuid4()

    # Cria o item no contexto do tenant A.
    with run_in_tenant_context(tenant_a.id):
        _equip_id, os_id = _criar_equip_cliente_e_os(tenant_a, equipamento_id=None)
        snapshot = ItemComercialOSSnapshot(
            id=item_id,
            tenant_id=tenant_a.id,
            os_id=os_id,
            tipo=TipoItemComercial.TAXA_VISITA,
            descricao_publica="Taxa de visita",
            valor=Decimal("50.00"),
            quantidade=2,
            origem_item_id=None,
        )
        repo.salvar_item_comercial(snapshot)

    # No contexto do tenant B, o item do tenant A deve ser invisivel.
    with run_in_tenant_context(tenant_b.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id FROM item_comercial_os WHERE id = %s",
                [str(item_id)],
            )
            row = cur.fetchone()

    assert row is None, (
        f"RLS cross-tenant falhou: tenant B conseguiu ver item {item_id} do tenant A"
    )


# =============================================================
# Teste (d) — indice parcial os_tenant_equip_idx existe no schema
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_osme_f1c_d_indice_parcial_os_tenant_equip_idx_existe():
    """(d) Indice parcial os_tenant_equip_idx existe apos migration 0019."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'ordens_servico'
              AND indexname = 'os_tenant_equip_idx'
            """
        )
        row = cur.fetchone()

    assert row is not None, "Indice os_tenant_equip_idx deve existir em ordens_servico"
    indexdef = row[1]
    assert "WHERE" in indexdef.upper(), (
        f"Indice deve ser PARCIAL (conter clausula WHERE), got: {indexdef}"
    )
    assert "null" in indexdef.lower() or "isnull" in indexdef.lower() or "is not null" in indexdef.lower() or "IS NOT NULL" in indexdef, (
        f"Indice parcial deve filtrar equipamento_id IS NOT NULL, got: {indexdef}"
    )
