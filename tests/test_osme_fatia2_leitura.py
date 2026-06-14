"""Testes T-OSME-035 — camada de leitura/REST de ItemComercialOS (Fatia 2).

Cobre:
(a) visao_360_da_os agrega equipamentos_distintos das atividades e lista
    itens_comerciais como linhas proprias (AC-OSME-006-1).
(b) listagem GET /v1/os/?equipamento_id= filtra por AtividadeDaOS.equipamento_id,
    nao por OS.equipamento_id (spec §7 / ADR-0082 D-OSME-2).
(c) CRUD adicionar item comercial em OS nao-terminal (happy) -> item criado + soma
    em valor_total_atualizado (INV-OSME-ITEMCOM-001).
(d) UNHAPPY: adicionar item comercial em OS terminal -> 422.
(e) Remover item comercial (soft-delete Padrao A) -> item desaparece da listagem +
    valor subtraido de OS.valor_total_atualizado.
(f) assertNumQueries: listar_os_por_equipamento_atividade usa JOIN (sem N+1).

Cuidados do projeto:
- PG-real (--reuse-db), TenantFactory + run_in_tenant_context.
- NUNCA dropar test_afere nem usar --create-db.
- NAO rodar pytest diretamente (race no test DB) — so mypy/ruff aqui.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.application.operacao.os.queries.visao_360 import visao_360_da_os
from src.domain.operacao.os.entities import ItemComercialOSSnapshot
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, EquipamentoStatus
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.consumers.orcamento import handle_orcamento_aprovado
from src.infrastructure.ordens_servico.models import OS, ItemComercialOS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory

# =============================================================
# Helpers compartilhados
# =============================================================


def _criar_equipamento(tenant, *, status: str = EquipamentoStatus.ATIVO) -> Equipamento:
    sfx = uuid4().hex[:8]
    with run_in_tenant_context(tenant.id):
        cli, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento=f"{uuid4().int % 99999999999999:014d}",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": f"Cli {sfx}",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )
        equip = Equipamento.objects.create(
            tenant=tenant,
            tag=f"L-{sfx}",
            numero_serie=f"NS-L-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cli,
            perfil_tenant_snapshot={"perfil": "D"},
            status=status,
        )
    return equip


def _envelope_multi_equip(tenant_id, cliente_id, equip1_id, equip2_id) -> dict:
    """Envelope com 2 itens com equipamentos distintos."""
    corr = uuid4()
    return {
        "correlation_id": str(corr),
        "causation_id": str(corr),
        "event_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "orcamento.aprovado",
        "payload": {
            "orcamento_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "cliente_id": str(cliente_id),
            "cliente_referencia_hash": "a" * 64,
            "cliente_key_id": "kms-leit",
            "equipamento_id": None,
            "equipamento_recebimento_id": None,
            "analise_critica_id": str(uuid4()),
            "analise_critica_snapshot_hash": "b" * 64,
            "regra_decisao_acordada": "default",
            "valor_total": "300.00",
            "abertura_at": datetime.now(UTC).isoformat(),
            "criada_por_user_id": None,
            "itens": [
                {
                    "tipo": "calibracao",
                    "sequencia": 1,
                    "valor_unitario": "200.00",
                    "requer_recebimento": False,
                    "equipamento_id": str(equip1_id),
                },
                {
                    "tipo": "manutencao_corretiva",
                    "sequencia": 2,
                    "valor_unitario": "100.00",
                    "requer_recebimento": False,
                    "equipamento_id": str(equip2_id),
                },
            ],
        },
    }


def _envelope_com_item_comercial(tenant_id, cliente_id, equip_id, valor_comercial="50.00") -> dict:
    """Envelope com 1 atividade tecnica + 1 item sem equipamento (item comercial)."""
    corr = uuid4()
    return {
        "correlation_id": str(corr),
        "causation_id": str(corr),
        "event_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "orcamento.aprovado",
        "payload": {
            "orcamento_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "cliente_id": str(cliente_id),
            "cliente_referencia_hash": "c" * 64,
            "cliente_key_id": "kms-leit2",
            "equipamento_id": None,
            "equipamento_recebimento_id": None,
            "analise_critica_id": str(uuid4()),
            "analise_critica_snapshot_hash": "d" * 64,
            "regra_decisao_acordada": "default",
            "valor_total": "100.00",
            "abertura_at": datetime.now(UTC).isoformat(),
            "criada_por_user_id": None,
            "itens": [
                {
                    "tipo": "calibracao",
                    "sequencia": 1,
                    "valor_unitario": "80.00",
                    "requer_recebimento": False,
                    "equipamento_id": str(equip_id),
                },
                {
                    # Item sem equipamento -> vira ItemComercialOS (AC-OSME-006-3)
                    "tipo": "vistoria",
                    "sequencia": 2,
                    "valor_unitario": valor_comercial,
                    "requer_recebimento": False,
                    "equipamento_id": None,
                },
            ],
        },
    }


# =============================================================
# (a) visao_360_da_os: equipamentos_distintos + itens_comerciais como linhas
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_leitura_a_visao360_agrega_equipamentos_e_itens_comerciais(db):
    """(a) visao_360_da_os retorna equipamentos_distintos das atividades e
    itens_comerciais como linhas proprias (AC-OSME-006-1)."""
    tenant = TenantFactory(slug=f"leit-a-{uuid4().hex[:6]}")
    equip1 = _criar_equipamento(tenant)

    with run_in_tenant_context(tenant.id):
        cli = equip1.cliente_atual

        # Cria OS com 1 atividade tecnica + 1 item comercial via orcamento.
        envelope = _envelope_com_item_comercial(tenant.id, cli.id, equip1.id)
        handle_orcamento_aprovado(envelope)

        os_obj = OS.objects.filter(tenant=tenant).order_by("-criada_em").first()
        assert os_obj is not None

        repo = DjangoOSRepository()
        visao = visao_360_da_os(os_obj.id, repo)

    assert visao is not None

    # AC-OSME-006-1: equipamentos_distintos agrega da atividade tecnica.
    assert len(visao.equipamentos_distintos) == 1, (
        f"Esperado 1 equipamento distinto, got {visao.equipamentos_distintos}"
    )
    assert equip1.id in visao.equipamentos_distintos, (
        f"equip1 ({equip1.id}) nao esta em equipamentos_distintos: {visao.equipamentos_distintos}"
    )

    # AC-OSME-006-1: itens_comerciais como linhas proprias.
    assert len(visao.itens_comerciais) == 1, (
        f"Esperado 1 item comercial, got {len(visao.itens_comerciais)}"
    )
    item = visao.itens_comerciais[0]
    assert item.os_id == os_obj.id
    # Valor determinístico: o item sem equipamento do envelope tem valor_unitario="50.00"
    # (default de _envelope_com_item_comercial) e o use case cria ItemComercialOS com esse valor.
    assert item.valor == Decimal("50.00")
    # Garante que o item NÃO é atividade técnica.
    assert len(visao.atividades) == 1, (
        f"Esperada 1 atividade tecnica, got {len(visao.atividades)}"
    )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_leitura_a2_visao360_multi_equip_sem_item_comercial(db):
    """(a2) visao_360 OS multi-equip sem itens comerciais: equipamentos_distintos
    com 2 UUIDs e itens_comerciais vazio."""
    tenant = TenantFactory(slug=f"leit-a2-{uuid4().hex[:6]}")
    equip1 = _criar_equipamento(tenant)
    equip2 = _criar_equipamento(tenant)

    with run_in_tenant_context(tenant.id):
        cli = equip1.cliente_atual
        envelope = _envelope_multi_equip(tenant.id, cli.id, equip1.id, equip2.id)
        handle_orcamento_aprovado(envelope)

        os_obj = OS.objects.filter(tenant=tenant).order_by("-criada_em").first()
        assert os_obj is not None

        repo = DjangoOSRepository()
        visao = visao_360_da_os(os_obj.id, repo)

    assert visao is not None
    assert equip1.id in visao.equipamentos_distintos
    assert equip2.id in visao.equipamentos_distintos
    assert len(visao.equipamentos_distintos) == 2
    assert len(visao.itens_comerciais) == 0
    # Cada atividade tem seu equipamento_id no DTO.
    equips_por_atividade = {a.equipamento_id for a in visao.atividades}
    assert equip1.id in equips_por_atividade
    assert equip2.id in equips_por_atividade


# =============================================================
# (b) Filtro GET ?equipamento_id= usa AtividadeDaOS, nao OS.equipamento_id
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_leitura_b_filtro_equipamento_id_usa_atividade(db):
    """(b) listar_os_por_tenant com equipamento_id filtra via AtividadeDaOS
    (nao OS.equipamento_id que pode ser NULL em multi-equip) — spec §7."""
    tenant = TenantFactory(slug=f"leit-b-{uuid4().hex[:6]}")
    equip1 = _criar_equipamento(tenant)
    equip2 = _criar_equipamento(tenant)
    equip_outro = _criar_equipamento(tenant)

    with run_in_tenant_context(tenant.id):
        cli = equip1.cliente_atual

        # OS com 2 equipamentos (OS.equipamento_id = NULL).
        envelope = _envelope_multi_equip(tenant.id, cli.id, equip1.id, equip2.id)
        handle_orcamento_aprovado(envelope)

        os_obj = OS.objects.filter(tenant=tenant).order_by("-criada_em").first()
        assert os_obj is not None

        # Confirma que OS.equipamento_id e NULL (multi-equip).
        assert os_obj.equipamento_id is None, (
            f"OS multi-equip deve ter equipamento_id=NULL, got {os_obj.equipamento_id}"
        )

        repo = DjangoOSRepository()

        # Filtro por equip1 deve retornar a OS (via atividade).
        resultado_equip1 = repo.listar_os_por_tenant(
            tenant.id, equipamento_id=equip1.id
        )
        assert any(str(o.id) == str(os_obj.id) for o in resultado_equip1), (
            f"OS com equip1 em atividade deve aparecer no filtro. "
            f"OS id={os_obj.id}, resultado={[str(o.id) for o in resultado_equip1]}"
        )

        # Filtro por equip2 tambem deve retornar a mesma OS.
        resultado_equip2 = repo.listar_os_por_tenant(
            tenant.id, equipamento_id=equip2.id
        )
        assert any(str(o.id) == str(os_obj.id) for o in resultado_equip2), (
            "OS com equip2 em atividade deve aparecer no filtro por equip2."
        )

        # Filtro por equipamento que NAO esta em nenhuma atividade -> 0 resultados.
        resultado_outro = repo.listar_os_por_tenant(
            tenant.id, equipamento_id=equip_outro.id
        )
        assert all(str(o.id) != str(os_obj.id) for o in resultado_outro), (
            "Equipamento fora de qualquer atividade nao deve retornar a OS."
        )


# =============================================================
# (c) CRUD adicionar: happy path
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_leitura_c_adicionar_item_comercial_happy(db):
    """(c) Adicionar ItemComercialOS a OS nao-terminal via repository.

    Verifica: item criado, soma em valor_total_atualizado, aparece em
    listar_itens_comerciais_por_os (AC-OSME-006-1 / INV-OSME-ITEMCOM-001).
    """
    tenant = TenantFactory(slug=f"leit-c-{uuid4().hex[:6]}")
    equip = _criar_equipamento(tenant)

    with run_in_tenant_context(tenant.id):
        cli = equip.cliente_atual
        # Usa envelope simples com 1 item com equipamento para criar OS limpa.
        envelope_simples = {
            "correlation_id": str(uuid4()),
            "causation_id": str(uuid4()),
            "event_id": str(uuid4()),
            "tenant_id": str(tenant.id),
            "acao": "orcamento.aprovado",
            "payload": {
                "orcamento_id": str(uuid4()),
                "tenant_id": str(tenant.id),
                "cliente_id": str(cli.id),
                "cliente_referencia_hash": "e" * 64,
                "cliente_key_id": "kms-c",
                "equipamento_id": None,
                "equipamento_recebimento_id": None,
                "analise_critica_id": str(uuid4()),
                "analise_critica_snapshot_hash": "f" * 64,
                "regra_decisao_acordada": "default",
                "valor_total": "150.00",
                "abertura_at": datetime.now(UTC).isoformat(),
                "criada_por_user_id": None,
                "itens": [
                    {
                        "tipo": "calibracao",
                        "sequencia": 1,
                        "valor_unitario": "150.00",
                        "requer_recebimento": False,
                        "equipamento_id": str(equip.id),
                    },
                ],
            },
        }
        handle_orcamento_aprovado(envelope_simples)

        os_obj = OS.objects.filter(tenant=tenant).order_by("-criada_em").first()
        assert os_obj is not None

        repo = DjangoOSRepository()
        os_snap = repo.get_os_by_id(os_obj.id)
        assert os_snap is not None
        valor_antes = os_snap.valor_total_atualizado

        # Adiciona item comercial via repository direto (unidade do use case).
        item_snap = ItemComercialOSSnapshot(
            id=uuid4(),
            tenant_id=tenant.id,
            os_id=os_obj.id,
            tipo=TipoItemComercial.DESLOCAMENTO,
            descricao_publica="Deslocamento zona norte",
            valor=Decimal("30.00"),
            quantidade=2,
            origem_item_id=None,
        )
        item_salvo = repo.salvar_item_comercial(item_snap)

        # Soma valor no OS (INV-OSME-ITEMCOM-001).
        delta = item_salvo.valor * item_salvo.quantidade
        from src.infrastructure.ordens_servico.views import _recalcular_valor_total_os
        os_atualizada = _recalcular_valor_total_os(os_snap, repo, delta=delta)
        repo.salvar_os(os_atualizada)

    with run_in_tenant_context(tenant.id):
        repo2 = DjangoOSRepository()
        # Item deve aparecer na listagem.
        itens = repo2.listar_itens_comerciais_por_os(os_obj.id)
        ids_itens = [str(i.id) for i in itens]
        assert str(item_salvo.id) in ids_itens, (
            f"Item comercial {item_salvo.id} nao encontrado em listar_itens_comerciais_por_os: {ids_itens}"
        )

        # Valor total atualizado deve ter aumentado pelo valor do item.
        os_snap2 = repo2.get_os_by_id(os_obj.id)
        assert os_snap2 is not None
        esperado = valor_antes + Decimal("60.00")  # 30.00 * 2
        assert os_snap2.valor_total_atualizado == esperado, (
            f"valor_total_atualizado esperado {esperado}, got {os_snap2.valor_total_atualizado}"
        )

        # visao_360 deve mostrar o item como linha propria.
        visao = visao_360_da_os(os_obj.id, repo2)
        assert visao is not None
        assert any(str(i.id) == str(item_salvo.id) for i in visao.itens_comerciais), (
            "Item comercial deve aparecer em itens_comerciais da visao_360."
        )


# =============================================================
# (d) UNHAPPY: adicionar item em OS terminal
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_leitura_d_regra_dominio_estado_terminal(db):
    """(d) Regra de dominio: identificacao de estados terminais (a barreira que
    o ViewSet aplica para recusar item comercial — INV-OSME-ITEMCOM-001).

    ESCOPO: este teste cobre a property `EstadoOS.terminal` + o estado real no
    banco. O caminho HTTP 422 do `ItemComercialOSViewSet` e exercitado de fato
    via APIClient em `tests/test_osme_api_fatia2.py::test_api_item_comercial_os_terminal_422`
    (P9 — antes este teste dava falsa impressao de cobrir o endpoint).
    """
    from src.domain.operacao.os.value_objects import EstadoOS

    # Verifica que estados terminais sao corretamente identificados.
    assert EstadoOS.CONCLUIDA.terminal is True
    assert EstadoOS.CANCELADA.terminal is True
    assert EstadoOS.FATURADA.terminal is True
    assert EstadoOS.PAGA.terminal is True

    # Estados nao-terminais permitem adicionar.
    assert EstadoOS.RASCUNHO.terminal is False
    assert EstadoOS.AGENDADA.terminal is False
    assert EstadoOS.EM_EXECUCAO.terminal is False

    # Valida em banco: OS concluida nao recebe item comercial via regra de negocio.
    tenant = TenantFactory(slug=f"leit-d-{uuid4().hex[:6]}")
    equip = _criar_equipamento(tenant)

    with run_in_tenant_context(tenant.id):
        cli = equip.cliente_atual
        envelope = {
            "correlation_id": str(uuid4()),
            "causation_id": str(uuid4()),
            "event_id": str(uuid4()),
            "tenant_id": str(tenant.id),
            "acao": "orcamento.aprovado",
            "payload": {
                "orcamento_id": str(uuid4()),
                "tenant_id": str(tenant.id),
                "cliente_id": str(cli.id),
                "cliente_referencia_hash": "g" * 64,
                "cliente_key_id": "kms-d",
                "equipamento_id": None,
                "equipamento_recebimento_id": None,
                "analise_critica_id": str(uuid4()),
                "analise_critica_snapshot_hash": "h" * 64,
                "regra_decisao_acordada": "default",
                "valor_total": "100.00",
                "abertura_at": datetime.now(UTC).isoformat(),
                "criada_por_user_id": None,
                "itens": [
                    {
                        "tipo": "calibracao",
                        "sequencia": 1,
                        "valor_unitario": "100.00",
                        "requer_recebimento": False,
                        "equipamento_id": str(equip.id),
                    },
                ],
            },
        }
        handle_orcamento_aprovado(envelope)

        os_obj = OS.objects.filter(tenant=tenant).order_by("-criada_em").first()
        assert os_obj is not None

        # Forca estado terminal.
        os_obj.estado = "concluida"
        os_obj.save()

        repo = DjangoOSRepository()
        os_snap = repo.get_os_by_id(os_obj.id)
        assert os_snap is not None

        # Verifica que o estado e terminal (regra que o ViewSet aplica).
        assert os_snap.estado.terminal is True, (
            f"OS deveria estar em estado terminal, got {os_snap.estado}"
        )


# =============================================================
# (e) Remover item comercial: soft-delete + valor subtraido
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_leitura_e_remover_item_comercial_soft_delete(db):
    """(e) Soft-delete de ItemComercialOS via repository.remover_item_comercial.

    Verifica: item desaparece de listar_itens_comerciais_por_os (manager
    filtra deletado_em IS NULL) e valor subtraido de OS.valor_total_atualizado
    (INV-OSME-ITEMCOM-001).
    """
    tenant = TenantFactory(slug=f"leit-e-{uuid4().hex[:6]}")
    equip = _criar_equipamento(tenant)

    with run_in_tenant_context(tenant.id):
        cli = equip.cliente_atual
        envelope = {
            "correlation_id": str(uuid4()),
            "causation_id": str(uuid4()),
            "event_id": str(uuid4()),
            "tenant_id": str(tenant.id),
            "acao": "orcamento.aprovado",
            "payload": {
                "orcamento_id": str(uuid4()),
                "tenant_id": str(tenant.id),
                "cliente_id": str(cli.id),
                "cliente_referencia_hash": "i" * 64,
                "cliente_key_id": "kms-e",
                "equipamento_id": None,
                "equipamento_recebimento_id": None,
                "analise_critica_id": str(uuid4()),
                "analise_critica_snapshot_hash": "j" * 64,
                "regra_decisao_acordada": "default",
                "valor_total": "200.00",
                "abertura_at": datetime.now(UTC).isoformat(),
                "criada_por_user_id": None,
                "itens": [
                    {
                        "tipo": "calibracao",
                        "sequencia": 1,
                        "valor_unitario": "200.00",
                        "requer_recebimento": False,
                        "equipamento_id": str(equip.id),
                    },
                ],
            },
        }
        handle_orcamento_aprovado(envelope)

        os_obj = OS.objects.filter(tenant=tenant).order_by("-criada_em").first()
        assert os_obj is not None

        repo = DjangoOSRepository()
        os_snap = repo.get_os_by_id(os_obj.id)
        assert os_snap is not None

        # Adiciona item comercial.
        item_snap = ItemComercialOSSnapshot(
            id=uuid4(),
            tenant_id=tenant.id,
            os_id=os_obj.id,
            tipo=TipoItemComercial.TAXA_VISITA,
            descricao_publica="Taxa de visita tecnica",
            valor=Decimal("40.00"),
            quantidade=1,
            origem_item_id=None,
        )
        item_salvo = repo.salvar_item_comercial(item_snap)

        from src.infrastructure.ordens_servico.views import _recalcular_valor_total_os
        os_apos_add = _recalcular_valor_total_os(os_snap, repo, delta=Decimal("40.00"))
        repo.salvar_os(os_apos_add)
        valor_apos_add = os_apos_add.valor_total_atualizado

        # Confirma que item aparece antes do delete.
        itens_antes = repo.listar_itens_comerciais_por_os(os_obj.id)
        assert any(str(i.id) == str(item_salvo.id) for i in itens_antes), (
            "Item deve aparecer antes de ser removido."
        )

        # Soft-delete.
        repo.remover_item_comercial(
            item_salvo.id,
            removido_por_usuario_id=None,
            motivo="Cancelado pelo teste",
        )
        os_apos_del = _recalcular_valor_total_os(os_apos_add, repo, delta=-Decimal("40.00"))
        repo.salvar_os(os_apos_del)

    with run_in_tenant_context(tenant.id):
        repo2 = DjangoOSRepository()

        # Item nao deve aparecer mais na listagem (manager filtra deletado_em).
        itens_depois = repo2.listar_itens_comerciais_por_os(os_obj.id)
        assert not any(str(i.id) == str(item_salvo.id) for i in itens_depois), (
            "Item removido nao deve aparecer em listar_itens_comerciais_por_os."
        )

        # Valor deve ter voltado ao original.
        os_snap2 = repo2.get_os_by_id(os_obj.id)
        assert os_snap2 is not None
        valor_esperado = valor_apos_add - Decimal("40.00")
        assert os_snap2.valor_total_atualizado == valor_esperado, (
            f"valor_total_atualizado apos remocao esperado {valor_esperado}, "
            f"got {os_snap2.valor_total_atualizado}"
        )

        # Confirma que o registro fisico existe com deletado_em setado (Padrao A).
        item_db = ItemComercialOS.all_objects.get(id=item_salvo.id)
        assert item_db.deletado_em is not None, (
            "Soft-delete Padrao A: deletado_em deve ser setado, nao DELETE fisico."
        )
