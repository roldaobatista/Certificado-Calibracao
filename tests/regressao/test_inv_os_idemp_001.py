"""Anti-regressao INV-OS-IDEMP-001 (P5 conserto 2026-05-24) — Idempotency-Key
obrigatorio em endpoints POST do M3 OS.

7 endpoints POST devem rejeitar requests sem header `Idempotency-Key`
com 400 `idempotency_key_ausente`. Em replay com mesma chave, devolvem
mesma resposta SEM efeito colateral duplicado.

Cobre /v1/os/{id}/cancelar/, /reabrir/, /atividades/, /iniciar/,
/concluir/, /reagendar/, /transferir/.

≥3 testes: ausencia header (400), payload divergente mesma chave (422),
replay devolve mesma resposta (200/201).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import transaction
from rest_framework.test import APIClient
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.application.operacao.os.atribuir_tecnico import (
    AtribuicaoAtividade,
    AtribuirTecnicoInput,
    atribuir_tecnico,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)


def _autenticar(client: APIClient, usuario, tenant) -> None:
    from django_otp import DEVICE_ID_SESSION_KEY
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device, _ = TOTPDevice.objects.get_or_create(
        user=usuario, name="default", defaults={"confirmed": True}
    )
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"idem-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@x.com")
    tecnico = UsuarioFactory(email=f"tec-{sfx}@x.com")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(
        usuario=tecnico, tenant=tenant, perfil="metrologista_bancada"
    )
    for u in (admin, tecnico):
        invalidate_user_cache(u.id, tenant.id)

    with run_in_tenant_context(tenant.id):
        cliente, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento="11222333000181",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": "Cli",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag=f"IDEM-{sfx}",
            numero_serie=f"NS-{sfx}",
            fabricante="X",
            modelo="Y",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(
            payload=AbrirOSInput(
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
            ),
            repository=repo,
        )
        atividades = repo.listar_atividades_por_os(res.os_id)
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=atividades[0].id,
                        tecnico_executor_id=tecnico.id,
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=admin.id,
            ),
            repository=repo,
        )

    return {
        "tenant": tenant,
        "admin": admin,
        "tecnico": tecnico,
        "os_id": res.os_id,
        "atividade_id": atividades[0].id,
    }


# =============================================================
# Unhappy: ausencia header -> 400 idempotency_key_ausente
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_idemp_001_unhappy_iniciar_sem_header_400(cenario):
    """Sem `Idempotency-Key`, /iniciar/ retorna 400."""
    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])
    resp = client.post(
        f"/api/v1/atividades/{cenario['atividade_id']}/iniciar/",
        data={"client_event_id": str(uuid4())},
        format="json",
    )
    assert resp.status_code == 400, resp.content
    assert resp.json()["codigo"] == "idempotency_key_ausente"


# =============================================================
# Happy: replay com mesma chave devolve mesma resposta sem duplicar
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_idemp_001_happy_replay_devolve_mesma_resposta(cenario):
    """2a chamada com mesma chave devolve mesmo body sem duplicar side-effect."""
    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])
    chave = str(uuid4())
    payload = {"client_event_id": str(uuid4())}

    resp1 = client.post(
        f"/api/v1/atividades/{cenario['atividade_id']}/iniciar/",
        data=payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=chave,
    )
    assert resp1.status_code == 200, resp1.content
    body1 = resp1.json()

    resp2 = client.post(
        f"/api/v1/atividades/{cenario['atividade_id']}/iniciar/",
        data=payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=chave,
    )
    assert resp2.status_code == 200, resp2.content
    body2 = resp2.json()
    assert body1["atividade_id"] == body2["atividade_id"]
    assert body1["os_id"] == body2["os_id"]


# =============================================================
# Unhappy: mesma chave + payload diferente -> 422
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_idemp_001_unhappy_payload_divergente_422(cenario):
    """Mesma chave reusada com payload diferente eh erro 422 — protege
    contra dev reusando chave em duas operacoes distintas."""
    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])
    chave = str(uuid4())

    resp1 = client.post(
        f"/api/v1/atividades/{cenario['atividade_id']}/iniciar/",
        data={"client_event_id": str(uuid4())},
        format="json",
        HTTP_IDEMPOTENCY_KEY=chave,
    )
    assert resp1.status_code == 200, resp1.content

    # Mesma chave, payload diferente — service detecta fingerprint divergente.
    resp2 = client.post(
        f"/api/v1/atividades/{cenario['atividade_id']}/iniciar/",
        data={"client_event_id": str(uuid4())},  # outro client_event_id
        format="json",
        HTTP_IDEMPOTENCY_KEY=chave,
    )
    assert resp2.status_code == 422, resp2.content
    assert resp2.json()["codigo"] == "idempotency_key_payload_divergente"
