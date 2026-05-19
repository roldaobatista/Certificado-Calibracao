"""US-CLI-004 — testes do bloqueio manual + automatico (14 cenarios T-CLI-030)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import (
    DjangoAuthorizationProvider,
    invalidate_user_cache,
)
from src.infrastructure.clientes.bloqueio import (
    MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
    MOTIVO_MANUAL_INADIMPLENCIA,
)
from src.infrastructure.clientes.models import Cliente, ClienteBloqueio, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

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
    if not device.confirmed:
        device.confirmed = True
        device.save()
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.fixture
def cenario(db):
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"bloq-{suffix}")
    admin = UsuarioFactory(email=f"adm-{suffix}@bloq.local")
    tecnico = UsuarioFactory(email=f"tec-{suffix}@bloq.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=tecnico, tenant=tenant, perfil="tecnico")
    invalidate_user_cache(admin.id, tenant.id)
    invalidate_user_cache(tecnico.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "tecnico": tecnico}


def _criar_cliente(tenant, usuario) -> Cliente:
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        return Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Bloqueio Teste",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )


def _payload_manual(motivo=MOTIVO_MANUAL_INADIMPLENCIA, **extra):
    base = {
        "motivo_categoria": motivo,
        "justificativa": "Cliente nao pagou 3 faturas e nao respondeu contato",
        "confirmacao_comunicacao_previa": True,
    }
    base.update(extra)
    return base


@pytest.mark.django_db(transaction=True)
def test_bloqueio_manual_exige_justificativa_minima_30_chars(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(justificativa="curta demais"),
        format="json",
    )
    assert response.status_code == 400, response.content
    assert response.json()["detail"] == "justificativa_muito_curta"


@pytest.mark.django_db(transaction=True)
def test_bloqueio_manual_exige_confirmacao_comunicacao_previa(cenario):
    """R3 advogado — CDC art. 6 III/IV + Lei 14.181/2021."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(confirmacao_comunicacao_previa=False),
        format="json",
    )
    assert response.status_code == 400, response.content
    assert response.json()["detail"] == "comunicacao_previa_obrigatoria"


@pytest.mark.django_db(transaction=True)
def test_bloqueio_persiste_estado_no_cliente(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(),
        format="json",
    )
    assert response.status_code == 201, response.content

    with run_in_tenant_context(cenario["tenant"].id):
        c = Cliente.objects.get(id=cliente.id)
        assert c.bloqueado is True
        ativo = ClienteBloqueio.objects.get(cliente=c, desbloqueado_em__isnull=True)
        assert ativo.motivo_categoria == MOTIVO_MANUAL_INADIMPLENCIA


@pytest.mark.django_db(transaction=True)
def test_bloqueio_audit_sem_pii_cru(cenario):
    """R1 advogado + TL6 — justificativa NAO vai cru pro audit, so hash."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    justif = "Cliente nao pagou 3 faturas e nao respondeu contato"
    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(justificativa=justif),
        format="json",
    )
    assert response.status_code == 201

    with run_in_tenant_context(cenario["tenant"].id):
        audit = Auditoria.objects.filter(
            action="cliente.bloqueado", resource_summary=str(cliente.id)
        ).first()
    assert audit is not None
    payload = audit.payload_jsonb
    assert justif not in str(payload), "Justificativa vazou cru no audit"
    assert payload["justificativa_hash"]
    # FA-A1: hash de PII versionado "vN:"+64hex (nao mais 64 cru).
    import re as _re

    assert _re.fullmatch(
        r"v[\w-]+:[0-9a-f]{64}", payload["justificativa_hash"]
    ), f"hash sem prefixo de versao FA-A1: {payload['justificativa_hash']!r}"
    assert payload["motivo_categoria"] == MOTIVO_MANUAL_INADIMPLENCIA
    assert payload["event_id"]


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_manual_funciona(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(),
        format="json",
    )
    response = client.post(
        f"/api/v1/clientes/{cliente.id}/desbloquear/",
        data={"motivo": "Cliente quitou todas as faturas em atraso"},
        format="json",
    )
    assert response.status_code == 200, response.content
    assert response.json()["ja_estava_desbloqueado"] is False

    with run_in_tenant_context(cenario["tenant"].id):
        c = Cliente.objects.get(id=cliente.id)
        assert c.bloqueado is False


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_audita_quem_desbloqueou(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(),
        format="json",
    )
    client.post(
        f"/api/v1/clientes/{cliente.id}/desbloquear/",
        data={"motivo": "Quitou as 3 faturas"},
        format="json",
    )

    with run_in_tenant_context(cenario["tenant"].id):
        audit = Auditoria.objects.filter(
            action="cliente.desbloqueado", resource_summary=str(cliente.id)
        ).first()
    assert audit is not None
    assert audit.payload_jsonb["usuario_id"] == str(cenario["admin"].id)


@pytest.mark.django_db(transaction=True)
def test_bloquear_exige_perfil_admin_tenant(cenario):
    """tecnico nao tem clientes.bloquear — 403."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(),
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_predicate_abac_can_denied_quando_cliente_bloqueado(cenario):
    """TL2 — provider.can(resource={'cliente_id':X}) denied quando bloqueado."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    # Bloqueia
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(),
        format="json",
    )

    # Usuario (tecnico) tenta os.criar — predicate detecta bloqueado
    # NOTA: perfil tecnico nao tem os.criar nesta US ainda. Reusamos os.ler
    # que existe e cobre o caminho ABAC.
    provider = DjangoAuthorizationProvider()
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["tecnico"].id):
        decision = provider.can(
            usuario_id=cenario["tecnico"].id,
            action="os.ler",
            resource={"cliente_id": str(cliente.id)},
            tenant_id=cenario["tenant"].id,
        )
    assert decision.allowed is False
    assert decision.reason == "cliente_bloqueado_manual"


@pytest.mark.django_db(transaction=True)
def test_predicate_abac_allowed_quando_cliente_nao_bloqueado(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    provider = DjangoAuthorizationProvider()
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["tecnico"].id):
        decision = provider.can(
            usuario_id=cenario["tecnico"].id,
            action="os.ler",
            resource={"cliente_id": str(cliente.id)},
            tenant_id=cenario["tenant"].id,
        )
    assert decision.allowed is True


@pytest.mark.django_db(transaction=True)
def test_idempotencia_no_op_bloquear_ja_bloqueado(cenario):
    """TL3 — bloquear cliente ja bloqueado = 200 com ja_estava_bloqueado=True."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    primeiro = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(),
        format="json",
    )
    assert primeiro.status_code == 201

    segundo = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(),
        format="json",
    )
    assert segundo.status_code == 200
    assert segundo.json()["ja_estava_bloqueado"] is True

    # E NAO criou novo registro
    with run_in_tenant_context(cenario["tenant"].id):
        ativos = ClienteBloqueio.objects.filter(
            cliente=cliente, desbloqueado_em__isnull=True
        ).count()
    assert ativos == 1


@pytest.mark.django_db(transaction=True)
def test_historico_bloqueio_preservado(cenario):
    """Bloqueia / desbloqueia / bloqueia de novo = 2 registros em cliente_bloqueios."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    client.post(f"/api/v1/clientes/{cliente.id}/bloquear/", data=_payload_manual(), format="json")
    client.post(f"/api/v1/clientes/{cliente.id}/desbloquear/", data={"motivo": "Quitou"}, format="json")
    client.post(f"/api/v1/clientes/{cliente.id}/bloquear/", data=_payload_manual(), format="json")

    with run_in_tenant_context(cenario["tenant"].id):
        total = ClienteBloqueio.objects.filter(cliente=cliente).count()
        ativos = ClienteBloqueio.objects.filter(
            cliente=cliente, desbloqueado_em__isnull=True
        ).count()
    assert total == 2
    assert ativos == 1


@pytest.mark.django_db(transaction=True)
def test_motivo_invalido_400(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(motivo="motivo_inventado"),
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "motivo_categoria_invalido"


@pytest.mark.django_db(transaction=True)
def test_observacao_com_cpf_rejeita(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data=_payload_manual(motivo_observacao="Cliente CPF 52998224725"),
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "motivo_observacao_com_pii"


@pytest.mark.django_db(transaction=True)
def test_job_automatico_respeita_flag_tenant_off(cenario, settings):
    """R3 advogado — tenant.bloqueio_automatico_inadimplencia_habilitado=False = job nao bloqueia."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    # Default eh False; explicit reconfirma
    cenario["tenant"].bloqueio_automatico_inadimplencia_habilitado = False
    cenario["tenant"].save()

    settings.INADIMPLENCIA_FONTE_INTERIM = [
        {
            "tenant_id": str(cenario["tenant"].id),
            "cliente_id": str(cliente.id),
            "dias_vencido": 95,
            "causation_titulo_id": str(uuid4()),
        }
    ]
    call_command("job_inadimplencia_alertas")

    with run_in_tenant_context(cenario["tenant"].id):
        assert not ClienteBloqueio.objects.filter(
            cliente=cliente, desbloqueado_em__isnull=True
        ).exists()


@pytest.mark.django_db(transaction=True)
def test_job_automatico_bloqueia_quando_flag_on(cenario, settings):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    cenario["tenant"].bloqueio_automatico_inadimplencia_habilitado = True
    cenario["tenant"].save()

    titulo_id = uuid4()
    settings.INADIMPLENCIA_FONTE_INTERIM = [
        {
            "tenant_id": str(cenario["tenant"].id),
            "cliente_id": str(cliente.id),
            "dias_vencido": 95,
            "causation_titulo_id": str(titulo_id),
        }
    ]
    call_command("job_inadimplencia_alertas")

    with run_in_tenant_context(cenario["tenant"].id):
        ativo = ClienteBloqueio.objects.get(
            cliente=cliente, desbloqueado_em__isnull=True
        )
        assert ativo.motivo_categoria == MOTIVO_AUTOMATICO_INADIMPLENCIA_90D
        assert ativo.causation_id == titulo_id
