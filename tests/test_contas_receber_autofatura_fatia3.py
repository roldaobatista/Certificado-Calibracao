"""Fatia 3a — auto-faturamento de OS (T-CR-040/041/042). Verificação 3a.

Cobre:
  - T-CR-040 enriquecimento do OUTBOX de os.concluida (cliente + valor faturável);
    valor = valor_total_atualizado (INV-OS-FAT-001 — NÃO valor_total); WORM intacto.
  - T-CR-041 consumer handle_os_concluida: cria Titulo (origem=OS), categoria por
    perfil do envelope, vencimento +30; idempotente por os_id; tenant suspenso →
    dead-letter; perfil None → fail-closed; valor 0 → no-op; publica titulo_emitido
    + os.faturada. handle_os_reaberta: cancela sem pagamento / mantém com pagamento.
  - T-CR-042 baixa manual de título de OS publica os.paga.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import connection
from rest_framework.test import APIClient
from src.domain.contas_receber.entities import Titulo
from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemTitulo,
)
from src.domain.contas_receber.erros import (
    PerfilIndeterminado,
    TenantSuspensoEmissaoBloqueada,
)
from src.domain.operacao.os.entities import EventoDeOSSnapshot
from src.domain.operacao.os.value_objects import TipoEventoDeOS
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.contas_receber.consumers.os_eventos import (
    handle_os_concluida,
    handle_os_reaberta,
)
from src.infrastructure.contas_receber.models import Pagamento as PagamentoModel
from src.infrastructure.contas_receber.models import Titulo as TituloModel
from src.infrastructure.contas_receber.repositories import DjangoTituloRepository
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import OS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository
from src.infrastructure.tenant.models import StatusLifecycle

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

_DBS = ["default", "breaker_writer"]


def _hash_cliente() -> str:
    """Valor fake de cliente_referencia_hash: 64 hex contíguos sem hífens — válido p/
    ReferenciaPIIAnonimizavel (len≥32). NÃO usa hashlib.sha256 (hook audit-pii-salt): é
    valor de teste, não PII real; o HMAC com salt por tenant é do código de produção."""
    return uuid4().hex + uuid4().hex


def _envelope_os_concluida(
    *,
    tenant_id,
    os_id,
    perfil: str | None = "A",
    valor_centavos: int = 150000,
    cliente_hash: str | None = None,
    cliente_id=None,
    event_id=None,
) -> dict:
    return {
        "event_id": str(event_id or uuid4()),
        "acao": "os.concluida",
        "perfil_no_evento": perfil,
        "tenant_id": str(tenant_id),
        "payload": {
            "os_id": str(os_id),
            "cliente_referencia_hash": cliente_hash or _hash_cliente(),
            "cliente_key_id": "v1",
            "cliente_atual_id": str(cliente_id) if cliente_id else None,
            "valor_total_centavos": valor_centavos,
        },
    }


def _envelope_os_reaberta(*, tenant_id, os_id) -> dict:
    return {
        "event_id": str(uuid4()),
        "acao": "os.reaberta",
        "tenant_id": str(tenant_id),
        "payload": {"os_id": str(os_id)},
    }


# ============================================================
# T-CR-041 — consumer handle_os_concluida
# ============================================================


@pytest.mark.django_db(transaction=True)
def test_os_concluida_cria_titulo_perfil_a():
    tenant = TenantFactory(perfil_a=True)
    os_id = uuid4()
    cliente_id = uuid4()
    chash = _hash_cliente()
    env = _envelope_os_concluida(
        tenant_id=tenant.id,
        os_id=os_id,
        perfil="A",
        valor_centavos=150000,
        cliente_hash=chash,
        cliente_id=cliente_id,
    )
    with run_in_tenant_context(tenant.id):
        handle_os_concluida(env)
        t = TituloModel.objects.get(tenant_id=tenant.id, os_id_origem=os_id)
        assert t.estado == EstadoTitulo.EMITIDO.value
        assert t.origem == OrigemTitulo.OS.value
        assert t.valor_original == 150000
        assert t.categoria_receita == CategoriaReceita.CALIBRACAO_RBC.value  # perfil A
        assert t.perfil_no_evento == "A"
        assert t.cliente_referencia_hash == chash
        assert str(t.cliente_atual_id) == str(cliente_id)
        assert t.meio == MeioCobranca.BOLETO.value
        # Vencimento = emissão + 30 dias (default ADR-0043)
        assert t.data_vencimento == t.data_emissao + timedelta(days=30)


@pytest.mark.django_db(transaction=True)
def test_os_concluida_perfil_b_categoria_nao_rbc():
    tenant = TenantFactory(perfil_b=True)
    os_id = uuid4()
    with run_in_tenant_context(tenant.id):
        handle_os_concluida(_envelope_os_concluida(tenant_id=tenant.id, os_id=os_id, perfil="B"))
        t = TituloModel.objects.get(tenant_id=tenant.id, os_id_origem=os_id)
        assert t.categoria_receita == CategoriaReceita.CALIBRACAO_NAO_RBC.value
        assert t.perfil_no_evento == "B"


@pytest.mark.django_db(transaction=True)
def test_os_concluida_idempotente_por_os_id():
    """2 eventos os.concluida (event_ids distintos) p/ a mesma OS → 1 só título."""
    tenant = TenantFactory(perfil_b=True)
    os_id = uuid4()
    with run_in_tenant_context(tenant.id):
        handle_os_concluida(_envelope_os_concluida(tenant_id=tenant.id, os_id=os_id, perfil="B"))
        handle_os_concluida(_envelope_os_concluida(tenant_id=tenant.id, os_id=os_id, perfil="B"))
        assert TituloModel.objects.filter(tenant_id=tenant.id, os_id_origem=os_id).count() == 1


@pytest.mark.django_db(transaction=True)
def test_os_concluida_tenant_suspenso_nao_cria_dead_letter():
    """R11 / ADR-0035: tenant suspenso → TenantSuspensoEmissaoBloqueada, sem título."""
    tenant = TenantFactory(perfil_b=True, status_lifecycle=StatusLifecycle.SUSPENSO)
    os_id = uuid4()
    with run_in_tenant_context(tenant.id):
        with pytest.raises(TenantSuspensoEmissaoBloqueada):
            handle_os_concluida(
                _envelope_os_concluida(tenant_id=tenant.id, os_id=os_id, perfil="B")
            )
        assert not TituloModel.objects.filter(tenant_id=tenant.id, os_id_origem=os_id).exists()


@pytest.mark.django_db(transaction=True)
def test_os_concluida_perfil_none_fail_closed():
    """D-CR-6: perfil ausente no envelope → PerfilIndeterminado (fail-closed)."""
    tenant = TenantFactory(perfil_a=True)
    os_id = uuid4()
    env = _envelope_os_concluida(tenant_id=tenant.id, os_id=os_id, perfil=None)
    with run_in_tenant_context(tenant.id):
        with pytest.raises(PerfilIndeterminado):
            handle_os_concluida(env)
        assert not TituloModel.objects.filter(tenant_id=tenant.id, os_id_origem=os_id).exists()


@pytest.mark.django_db(transaction=True)
def test_os_concluida_valor_zero_sem_titulo():
    """OS sem valor faturável (todas atividades canceladas — INV-OS-FAT-001) → no-op."""
    tenant = TenantFactory(perfil_b=True)
    os_id = uuid4()
    with run_in_tenant_context(tenant.id):
        handle_os_concluida(
            _envelope_os_concluida(tenant_id=tenant.id, os_id=os_id, perfil="B", valor_centavos=0)
        )
        assert not TituloModel.objects.filter(tenant_id=tenant.id, os_id_origem=os_id).exists()


@pytest.mark.django_db(transaction=True)
def test_os_concluida_publica_titulo_emitido_e_os_faturada():
    tenant = TenantFactory(perfil_a=True)
    os_id = uuid4()
    event_id = uuid4()
    with run_in_tenant_context(tenant.id):
        handle_os_concluida(
            _envelope_os_concluida(
                tenant_id=tenant.id, os_id=os_id, perfil="A", event_id=event_id
            )
        )
        with connection.cursor() as cur:
            cur.execute(
                "SELECT acao FROM bus_outbox WHERE causation_id = %s ORDER BY acao",
                [str(event_id)],
            )
            acoes = {r[0] for r in cur.fetchall()}
        assert "contas_receber.titulo_emitido" in acoes
        assert "os.faturada" in acoes


# ============================================================
# T-CR-041 — consumer handle_os_reaberta
# ============================================================


@pytest.mark.django_db(transaction=True)
def test_os_reaberta_cancela_titulo_sem_pagamento():
    tenant = TenantFactory(perfil_b=True)
    os_id = uuid4()
    with run_in_tenant_context(tenant.id):
        handle_os_concluida(_envelope_os_concluida(tenant_id=tenant.id, os_id=os_id, perfil="B"))
        t = TituloModel.objects.get(tenant_id=tenant.id, os_id_origem=os_id)
        assert t.estado == EstadoTitulo.EMITIDO.value
        handle_os_reaberta(_envelope_os_reaberta(tenant_id=tenant.id, os_id=os_id))
        t.refresh_from_db()
        assert t.estado == EstadoTitulo.CANCELADO.value


@pytest.mark.django_db(transaction=True)
def test_os_reaberta_com_pagamento_mantem_titulo():
    """AC-CR-006-2: título com pagamento NÃO é cancelado na reabertura."""
    tenant = TenantFactory(perfil_b=True)
    os_id = uuid4()
    with run_in_tenant_context(tenant.id):
        handle_os_concluida(_envelope_os_concluida(tenant_id=tenant.id, os_id=os_id, perfil="B"))
        t = TituloModel.objects.get(tenant_id=tenant.id, os_id_origem=os_id)
        PagamentoModel.objects.create(
            id=uuid4(),
            tenant_id=tenant.id,
            titulo_id=t.id,
            valor=50000,
            data=date.today(),
            origem="manual",
            valor_atualizado_snapshot_em_pagamento=50000,
            gateway_event_id="",
            comprovante_url="",
        )
        handle_os_reaberta(_envelope_os_reaberta(tenant_id=tenant.id, os_id=os_id))
        t.refresh_from_db()
        assert t.estado == EstadoTitulo.EMITIDO.value  # mantido


@pytest.mark.django_db(transaction=True)
def test_os_reaberta_sem_titulo_noop():
    tenant = TenantFactory(perfil_b=True)
    os_id = uuid4()
    with run_in_tenant_context(tenant.id):
        # Nenhum título para a OS — não levanta
        handle_os_reaberta(_envelope_os_reaberta(tenant_id=tenant.id, os_id=os_id))
        assert not TituloModel.objects.filter(tenant_id=tenant.id, os_id_origem=os_id).exists()


# ============================================================
# T-CR-040 — enriquecimento do OUTBOX de os.concluida
# ============================================================


def _criar_os(*, tenant, valor_total: str, valor_total_atualizado: str, cliente_id, chash) -> OS:
    return OS.objects.create(
        tenant_id=tenant.id,
        numero_os=uuid4().int % 1_000_000_000,
        cliente_id=cliente_id,
        cliente_referencia_hash=chash,
        cliente_key_id="v1",
        estado="concluida",
        tipo_predominante="calibracao",
        valor_total=Decimal(valor_total),
        valor_total_atualizado=Decimal(valor_total_atualizado),
    )


def _publicar_os_concluida(repo: DjangoOSRepository, *, tenant, os_obj) -> EventoDeOSSnapshot:
    snap = EventoDeOSSnapshot(
        id=uuid4(),
        tenant_id=tenant.id,
        os_id=os_obj.id,
        atividade_id=None,
        tipo=TipoEventoDeOS.OS_CONCLUIDA,
        payload_hash="hash-teste",
        payload_data={"tipo_predominante": "calibracao", "nao_conformidade_global": False},
        correlation_id=uuid4(),
        actor_user_id=None,
        occurred_at=datetime.now(UTC),
        criado_em=datetime.now(UTC),
    )
    return repo.publicar_evento(snap)


@pytest.mark.django_db(transaction=True)
def test_t_cr_040_outbox_enriquecido_com_cliente_e_valor():
    tenant = TenantFactory(perfil_b=True)
    cliente_id = uuid4()
    chash = _hash_cliente()
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id):
        os_obj = _criar_os(
            tenant=tenant,
            valor_total="1500.00",
            valor_total_atualizado="1500.00",
            cliente_id=cliente_id,
            chash=chash,
        )
        snap = _publicar_os_concluida(repo, tenant=tenant, os_obj=os_obj)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb FROM bus_outbox WHERE causation_id = %s AND acao = %s",
                [str(snap.id), "os.concluida"],
            )
            row = cur.fetchone()
    assert row is not None, "evento os.concluida não chegou ao outbox"
    import json as _json

    env = row[0] if isinstance(row[0], dict) else _json.loads(row[0])
    payload = env["payload"]
    assert payload["cliente_referencia_hash"] == chash
    assert payload["cliente_key_id"] == "v1"
    assert str(payload["cliente_atual_id"]) == str(cliente_id)
    assert payload["valor_total_centavos"] == 150000
    # WORM minimalista preservado no payload do outbox (spread do payload_data)
    assert payload["tipo_predominante"] == "calibracao"


@pytest.mark.django_db(transaction=True)
def test_t_cr_040_valor_e_o_atualizado_nao_o_total_inv_os_fat_001():
    """INV-OS-FAT-001: cobra valor_total_atualizado (atividade cancelada NÃO entra),
    nunca o valor_total snapshot original."""
    tenant = TenantFactory(perfil_b=True)
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id):
        os_obj = _criar_os(
            tenant=tenant,
            valor_total="2000.00",  # snapshot original
            valor_total_atualizado="1500.00",  # após cancelar atividade de R$ 500
            cliente_id=uuid4(),
            chash=_hash_cliente(),
        )
        snap = _publicar_os_concluida(repo, tenant=tenant, os_obj=os_obj)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb FROM bus_outbox WHERE causation_id = %s AND acao = %s",
                [str(snap.id), "os.concluida"],
            )
            row = cur.fetchone()
    import json as _json

    env = row[0] if isinstance(row[0], dict) else _json.loads(row[0])
    assert env["payload"]["valor_total_centavos"] == 150000  # atualizado, NÃO 200000


# ============================================================
# T-CR-042 — baixa manual de título de OS publica os.paga
# ============================================================


def _autenticar(client: APIClient, usuario, tenant) -> None:
    from django_otp import DEVICE_ID_SESSION_KEY
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device, _ = TOTPDevice.objects.get_or_create(
        user=usuario, name="default", defaults={"confirmed": True}
    )
    if not device.confirmed:
        device.confirmed = True
        device.save()
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_t_cr_042_baixa_manual_titulo_de_os_publica_os_paga():
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_b=True, slug=f"cr-osp-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@cr.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)

    os_id = uuid4()
    titulo_id = uuid4()
    # Cria título de OS direto (origem=OS, os_id_origem) — molde do consumer.
    with run_in_tenant_context(tenant.id):
        titulo = Titulo(
            titulo_id=titulo_id,
            tenant_id=tenant.id,
            cliente_referencia=ReferenciaPIIAnonimizavel(
                uuid_atual_id=uuid4(), hash_original=_hash_cliente(), key_id="v1"
            ),
            valor_original=Dinheiro(centavos=150000, moeda="BRL"),
            data_emissao=date.today(),
            data_vencimento=date.today() + timedelta(days=30),
            estado=EstadoTitulo.EMITIDO,
            meio=MeioCobranca.BOLETO,
            categoria_receita=CategoriaReceita.CALIBRACAO_NAO_RBC,
            perfil_no_evento="B",
            origem=OrigemTitulo.OS,
            os_id_origem=os_id,
            revision=0,
            criado_em=datetime.now(UTC),
        )
        DjangoTituloRepository().salvar_novo_titulo(titulo)

    client = APIClient()
    _autenticar(client, admin, tenant)
    r = client.post(
        f"/api/v1/contas-receber/{titulo_id}/baixar-manual/",
        {"valor_centavos": 150000, "data_pagamento": date.today().isoformat()},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert r.status_code == 200, r.content
    assert r.json()["estado"] == EstadoTitulo.PAGO.value

    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM bus_outbox WHERE acao = %s AND envelope_jsonb->'payload'->>'os_id' = %s",
                ["os.paga", str(os_id)],
            )
            assert cur.fetchone() is not None, "os.paga não publicado na baixa manual de título de OS"
