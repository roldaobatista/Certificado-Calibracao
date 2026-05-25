"""Anti-regressao INV-OS-SYNC-001 (T-OS-120b) — fotos append-only.

INV-OS-SYNC-001: `EvidenciaFotoAtividade` segue Padrao B (ADR-0031):
- INSERT permitido em qualquer estado da atividade.
- UPDATE bloqueado por trigger (`evidencia_foto_atividade_append_only_trg`)
  exceto setar `revogado_em` UMA UNICA VEZ (LGPD art. 18 — face cliente).
- DELETE bloqueado completamente.
- LWW so se aplica a campos escalares da AtividadeDaOS — foto NUNCA
  perde no merge sync mobile.

≥3 testes: happy (INSERT + revogar uma vez OK), unhappy update (mudar
b2_uri raises), unhappy delete (raises), cross-tenant (foto tenant A
nao aparece em tenant B via RLS).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import ProgrammingError, transaction
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import EvidenciaFotoAtividade
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
            tag=f"INV-SYN-{sfx}",
            numero_serie=f"NS-SYN-{sfx}",
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


def _criar_foto(tenant, atividade_id, *, sufixo: str = "") -> EvidenciaFotoAtividade:
    """Cria EvidenciaFotoAtividade dentro do contexto do tenant."""
    with run_in_tenant_context(tenant.id):
        return EvidenciaFotoAtividade.objects.create(
            tenant=tenant,
            atividade_id=atividade_id,
            tipo="conclusao",
            b2_uri=f"https://b2.example.com/foto-{sufixo or uuid4().hex[:6]}.jpg",
            foto_sha256="f" * 64,
            client_event_id=uuid4(),
            client_event_created_at=datetime.now(UTC),
            enviada_em=datetime.now(UTC),
        )


# =============================================================
# Happy: INSERT + revogar uma vez OK
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_sync_001_happy_insert_e_revogar_uma_vez(db):
    """Happy: criar foto + revogar `revogado_em` UMA UNICA VEZ funciona
    (LGPD art. 18 — face cliente)."""
    tenant = TenantFactory(slug=f"inv-syn-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    ativ_id = _abrir_e_pegar_atividade(tenant, cliente, equipamento)

    foto = _criar_foto(tenant, ativ_id)
    assert foto.revogado_em is None

    # Revogar (LGPD art. 18) eh permitido.
    agora = datetime.now(UTC)
    with run_in_tenant_context(tenant.id):
        EvidenciaFotoAtividade.objects.filter(id=foto.id).update(revogado_em=agora)
        foto.refresh_from_db()
    assert foto.revogado_em is not None


# =============================================================
# Unhappy update: mudar campo nao-revogado_em raises
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_sync_001_unhappy_update_b2_uri_bloqueado(db):
    """Unhappy: trigger PG raises ao tentar UPDATE de b2_uri (campo
    nao-revogado_em). EvidenciaFotoAtividade eh append-only."""
    tenant = TenantFactory(slug=f"inv-syn-u-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    ativ_id = _abrir_e_pegar_atividade(tenant, cliente, equipamento)
    foto = _criar_foto(tenant, ativ_id)

    with run_in_tenant_context(tenant.id), pytest.raises(ProgrammingError) as exc:
        EvidenciaFotoAtividade.objects.filter(id=foto.id).update(
            b2_uri="https://b2.example.com/alterada.jpg"
        )
    msg = str(exc.value).lower()
    assert "append-only" in msg or "so revogado_em pode mudar" in msg


# =============================================================
# Unhappy delete: trigger PG raises em DELETE
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_sync_001_unhappy_delete_bloqueado(db):
    """Unhappy: trigger PG raises em DELETE (B2 WORM 25a)."""
    tenant = TenantFactory(slug=f"inv-syn-d-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    ativ_id = _abrir_e_pegar_atividade(tenant, cliente, equipamento)
    foto = _criar_foto(tenant, ativ_id)

    with run_in_tenant_context(tenant.id), pytest.raises(ProgrammingError) as exc:
        EvidenciaFotoAtividade.objects.filter(id=foto.id).delete()
    msg = str(exc.value).lower()
    assert "nao pode ser deletada" in msg or "b2 worm" in msg


# =============================================================
# Cross-tenant: foto criada em tenant A nao aparece em tenant B
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_sync_001_cross_tenant_foto_isolada(db):
    """Cross-tenant: foto em tenant A nao eh visivel em tenant B (RLS)."""
    tenant_a = TenantFactory(slug=f"inv-syn-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-syn-ctb-{uuid4().hex[:6]}")
    cli_a, eq_a = _setup(tenant_a)
    cli_b, eq_b = _setup(tenant_b)
    ativ_a = _abrir_e_pegar_atividade(tenant_a, cli_a, eq_a)
    ativ_b = _abrir_e_pegar_atividade(tenant_b, cli_b, eq_b)
    foto_a = _criar_foto(tenant_a, ativ_a, sufixo="a")
    foto_b = _criar_foto(tenant_b, ativ_b, sufixo="b")

    with run_in_tenant_context(tenant_a.id):
        ids_a = set(EvidenciaFotoAtividade.objects.values_list("id", flat=True))
    with run_in_tenant_context(tenant_b.id):
        ids_b = set(EvidenciaFotoAtividade.objects.values_list("id", flat=True))

    assert foto_a.id in ids_a
    assert foto_b.id in ids_b
    assert foto_a.id not in ids_b, "foto tenant A nao deveria aparecer em B (RLS)"
    assert foto_b.id not in ids_a, "foto tenant B nao deveria aparecer em A (RLS)"
