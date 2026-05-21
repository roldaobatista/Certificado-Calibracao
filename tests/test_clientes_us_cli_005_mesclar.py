"""US-CLI-005 — testes do endpoint POST /clientes/{vencedor}/mesclar/{perdedor}/.

9 testes (T-CLI-018 do plano):
1. test_mesclar_aplica_sobrescritas_no_vencedor
2. test_mesclar_soft_deleta_perdedor
3. test_mesclar_publica_evento_sem_pii (R1 advogado)
4. test_mesclar_cross_tenant_bloqueado (TL5)
5. test_mesclar_exige_perfil_admin_tenant
6. test_mesclar_motivo_categoria_obrigatorio_enum
7. test_mesclar_observacao_com_cpf_rejeita_400 (R2 advogado)
8. test_unique_index_parcial_permite_reativacao_de_documento (TL3 + R4)
9. test_mesclar_atomico_rollback_em_falha (TL6)
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
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
    tenant = TenantFactory(slug=f"mesc-{suffix}")
    admin = UsuarioFactory(email=f"adm-{suffix}@mesc.local")
    tecnico = UsuarioFactory(email=f"tec-{suffix}@mesc.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=tecnico, tenant=tenant, perfil="tecnico")
    invalidate_user_cache(admin.id, tenant.id)
    invalidate_user_cache(tecnico.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "tecnico": tecnico}


def _criar_par(tenant, usuario):
    """Cria 2 clientes PJ no mesmo tenant pra usar como vencedor + perdedor."""
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        venc = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Vencedor LTDA",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        perd = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="33000167000101",
            nome="Perdedor LTDA",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
    return venc, perd


@pytest.mark.django_db(transaction=True)
def test_mesclar_aplica_sobrescritas_no_vencedor(cenario):
    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "sobrescrever": {"nome": "Nome Novo do Vencedor"},
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 200, response.content

    with run_in_tenant_context(cenario["tenant"].id):
        venc_pos = Cliente.objects.get(id=venc.id)
    assert venc_pos.nome == "Nome Novo do Vencedor"


@pytest.mark.django_db(transaction=True)
def test_mesclar_soft_deleta_perdedor(cenario):
    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "sobrescrever": {},
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 200, response.content

    with run_in_tenant_context(cenario["tenant"].id):
        # default manager nao vê perdedor
        assert not Cliente.objects.filter(id=perd.id).exists()
        # all_objects ve
        perd_pos = Cliente.all_objects.get(id=perd.id)
    assert perd_pos.deletado_em is not None
    assert perd_pos.deletado_motivo_categoria == "duplicacao_atendimento"


@pytest.mark.django_db(transaction=True)
def test_mesclar_publica_evento_sem_pii(cenario):
    """R1 advogado: audit grava action='cliente.mesclado' sem PII cru."""
    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "sobrescrever": {"nome": "X", "email": "abc@def.com"},
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 200, response.content

    with run_in_tenant_context(cenario["tenant"].id):
        audit = Auditoria.objects.filter(
            action="cliente.mesclado",
            resource_summary=str(venc.id),
        ).first()
    assert audit is not None
    payload = audit.payload_jsonb

    # Sem CNPJ cru
    assert "11222333000181" not in str(payload)
    assert "33000167000101" not in str(payload)
    # Sem nome do perdedor cru
    assert "Perdedor LTDA" not in str(payload)
    # Sem valores das sobrescritas
    assert "abc@def.com" not in str(payload)
    # Mas TEM as keys + hashes
    assert sorted(payload["campos_sobrescritos_keys"]) == ["email", "nome"]
    assert payload["motivo_categoria"] == "duplicacao_atendimento"
    assert payload["perdedor_documento_hash"]
    assert payload["perdedor_nome_hash"]


@pytest.mark.django_db(transaction=True)
def test_mesclar_cross_tenant_bloqueado(cenario):
    """TL5 — vencedor tenant A, perdedor tenant B = 403/404 (defesa em profundidade)."""
    # cria perdedor em outro tenant
    suffix = uuid4().hex[:8]
    tenant_b = TenantFactory(slug=f"b-mesc-{suffix}")
    with run_in_tenant_context(tenant_b.id):
        perd_b = Cliente.objects.create(
            tenant=tenant_b,
            tipo_pessoa=TipoPessoa.PJ,
            documento="33000167000101",
            nome="Perdedor B LTDA",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )

    # vencedor em tenant A do cenario
    venc, _ = _criar_par(cenario["tenant"], cenario["admin"])

    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd_b.id}/",
        data={
            "sobrescrever": {},
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    # RLS faz perd_b nao ser encontravel → 404; defesa adicional do use case
    # bate 403 se passar pela RLS. Aceitamos qualquer dos 2 (sao defesas).
    assert response.status_code in (403, 404), response.content


@pytest.mark.django_db(transaction=True)
def test_mesclar_exige_perfil_admin_tenant(cenario):
    """tecnico nao tem clientes.mesclar — 403."""
    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "sobrescrever": {},
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 403, response.content


@pytest.mark.django_db(transaction=True)
def test_mesclar_motivo_categoria_obrigatorio_enum(cenario):
    """Motivo invalido = 400."""
    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "sobrescrever": {},
            "motivo_categoria": "motivo_inventado",
        },
        format="json",
    )
    assert response.status_code == 400, response.content
    assert response.json()["detail"] == "motivo_categoria_invalido"


@pytest.mark.django_db(transaction=True)
def test_mesclar_observacao_com_cpf_rejeita_400(cenario):
    """R2 advogado — observacao com PII = 400."""
    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "sobrescrever": {},
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
            "motivo_observacao": "Cliente CPF 52998224725 mudou de email",
        },
        format="json",
    )
    assert response.status_code == 400, response.content
    assert response.json()["detail"] == "motivo_observacao_com_pii"


@pytest.mark.django_db(transaction=True)
def test_unique_index_parcial_permite_reativacao_de_documento(cenario):
    """TL3 + R4 — apos soft-delete, documento pode ser reusado em novo cadastro."""
    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])
    doc_perd = perd.documento

    # Mescla — perdedor vira soft-deleted
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "sobrescrever": {},
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 200, response.content

    # Cria novo cliente com o mesmo CNPJ do perdedor — UNIQUE parcial permite
    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": doc_perd,
            "nome": "Reativado LTDA",
            "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
        },
        format="json",
    )
    assert response.status_code == 201, response.content


@pytest.mark.django_db(transaction=True)
def test_mesclar_atomico_rollback_em_falha(cenario, monkeypatch):
    """TL6 — falha no audit faz rollback do soft-delete e sobrescritas."""
    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])

    # Monkey-patch pra forcar erro no registrar_auditoria APENAS pra 'cliente.mesclado'
    from src.infrastructure.audit import services

    original = services.registrar_auditoria

    def falha_apenas_mesclado(*args, **kwargs):  # type: ignore[no-untyped-def] -- closure de monkeypatch com assinatura dinamica pytest
        if kwargs.get("action") == "cliente.mesclado":
            raise RuntimeError("Audit falhou simulado")
        return original(*args, **kwargs)

    monkeypatch.setattr(services, "registrar_auditoria", falha_apenas_mesclado)
    # E re-importa no namespace que a view importou

    monkeypatch.setattr(
        "src.infrastructure.audit.services.registrar_auditoria",
        falha_apenas_mesclado,
    )

    client = APIClient(raise_request_exception=False)
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "sobrescrever": {"nome": "NaoDeveriaSalvar"},
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 500

    # Rollback efetivo: perdedor NAO foi soft-deleted, vencedor mantem nome
    with run_in_tenant_context(cenario["tenant"].id):
        perd_pos = Cliente.all_objects.get(id=perd.id)
        venc_pos = Cliente.objects.get(id=venc.id)
    assert perd_pos.deletado_em is None, "Rollback falhou — perdedor foi soft-deleted"
    assert venc_pos.nome == "Vencedor LTDA", "Rollback falhou — vencedor foi alterado"


# =============================================================
# CONCERN Auditor Qualidade US-CLI-005 retroativa (2026-05-18) —
# 4 ramos ErroMesclagem sem teste de mapeamento HTTP status.
# Sem cobertura, troca de status passa verde silenciosamente.
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_mesclar_mesma_entidade_retorna_400(cenario):
    """ErroMesclagem(mesma_entidade) -> HTTP 400."""
    venc, _ = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{venc.id}/",
        data={
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "mesma_entidade"


@pytest.mark.django_db(transaction=True)
def test_mesclar_vencedor_nao_encontrado_retorna_404(cenario):
    """ErroMesclagem(vencedor_nao_encontrado) -> HTTP 404."""
    _, perd = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    inexistente = uuid4()
    response = client.post(
        f"/api/v1/clientes/{inexistente}/mesclar/{perd.id}/",
        data={
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "vencedor_nao_encontrado"


@pytest.mark.django_db(transaction=True)
def test_mesclar_perdedor_nao_encontrado_retorna_404(cenario):
    """ErroMesclagem(perdedor_nao_encontrado) -> HTTP 404."""
    venc, _ = _criar_par(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    inexistente = uuid4()
    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{inexistente}/",
        data={
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "perdedor_nao_encontrado"


@pytest.mark.django_db(transaction=True)
def test_mesclar_perdedor_ja_deletado_retorna_409(cenario):
    """ErroMesclagem(perdedor_ja_deletado) -> HTTP 409.

    Idempotencia reversa: tentar mesclar de novo o mesmo par retorna 409.
    """

    venc, perd = _criar_par(cenario["tenant"], cenario["admin"])
    # Marca perdedor como ja soft-deleted
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        Cliente.all_objects.filter(id=perd.id).update(
            deletado_em=datetime.now(UTC),
            deletado_motivo_categoria="duplicacao_atendimento",
        )

    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{venc.id}/mesclar/{perd.id}/",
        data={
            "motivo_categoria": "duplicacao_atendimento",
            "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
        },
        format="json",
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "perdedor_ja_deletado"
