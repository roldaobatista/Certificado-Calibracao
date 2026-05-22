"""T-EQP-042+043+045+046 — sucatamento de equipamento (US-EQP-005).

Cobre:
- AC-EQP-005-1: POST `/sucatear/` sem cert vigente -> 200 + estado
  terminal + evento `equipamento.sucateado`.
- AC-EQP-005-2 + P-EQP-S9: cert vigente exige `confirmacao_dupla=True`
  E `ciencia_validade_tecnica_registrada=True`; ausente -> 422 com
  texto canonico do modal + `texto_modal_versao_id`.
- AC-EQP-005-2: cert vigente publica adicionalmente
  `equipamento.sucateado_com_cert_vigente`.
- AC-EQP-005-3 (INV-INT-002): trigger PG `transicao_status_permitida`
  ja bloqueia transicoes invalidas; cobre `sucata->extraviado` OK e
  `sucata->ativo` bloqueado (regressao do migration 0002).
- AC-EQP-005-5 / P-EQP-R8: `ciencia_validade_tecnica_registrada=True`
  obrigatorio quando tem_cert.
- AC-EQP-005-4: helper `texto_modal_sucatamento_cert_vigente` retorna
  texto canonico (anti-drift versao).
- Justificativa <30 chars / PII -> 400.
- Authz `equipamentos.sucatear` -> 403 sem perfil.
- Trigger PG imutabilidade pos-INSERT -> UPDATE no sucatamento
  bloqueado.
- Payload sanitizado (cliente_atual_id NUNCA aparece).
- RLS cross-tenant -> 404.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.certificados.models import Certificado, StatusCertificado
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    EquipamentoSucatamento,
)
from src.infrastructure.equipamentos.validators import (
    TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE,
    TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA,
    texto_modal_sucatamento_cert_vigente,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory


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
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"suc-a-{sfx}", nome_fantasia="Lab Suc A")
    admin_a = UsuarioFactory(email=f"adm-suc-{sfx}@e.local")
    leitor_a = UsuarioFactory(email=f"ler-suc-{sfx}@e.local")
    UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(
        usuario=leitor_a, tenant=tenant_a, perfil="cliente_externo_leitura"
    )
    for u in [admin_a, leitor_a]:
        invalidate_user_cache(u.id, tenant_a.id)

    with run_in_tenant_context(tenant_a.id):
        cliente = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Suc",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq_sem_cert = Equipamento.objects.create(
            tenant=tenant_a,
            tag=f"SUC-SC-{sfx}",
            numero_serie=f"NS-SC-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
        eq_com_cert = Equipamento.objects.create(
            tenant=tenant_a,
            tag=f"SUC-CC-{sfx}",
            numero_serie=f"NS-CC-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
        from django.utils import timezone

        Certificado.objects.create(
            tenant=tenant_a,
            equipamento=eq_com_cert,
            status=StatusCertificado.EMITIDO.value,
            emitido_em=timezone.now(),
        )
    return {
        "tenant_a": tenant_a,
        "admin_a": admin_a,
        "leitor_a": leitor_a,
        "cliente": cliente,
        "eq_sem_cert": eq_sem_cert,
        "eq_com_cert": eq_com_cert,
    }


# ====================================================================
# T-EQP-042 — sucatar sem cert vigente (happy)
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_sucatar_sem_cert_happy(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {
            "justificativa": (
                "Equipamento com defeito irreversivel na celula de carga "
                "conforme laudo tecnico anexo ao processo."
            ),
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["status"] == "sucata"
    assert body["tem_cert_vigente_no_momento"] is False
    assert body["sucatamento_id"]
    with run_in_tenant_context(cenario["tenant_a"].id):
        cenario["eq_sem_cert"].refresh_from_db()
        assert cenario["eq_sem_cert"].status == "sucata"
        suc = EquipamentoSucatamento.objects.get(
            equipamento_id=cenario["eq_sem_cert"].id
        )
    assert suc.tem_cert_vigente_no_momento is False
    assert suc.confirmacao_dupla is False
    assert suc.ciencia_validade_tecnica_registrada is False
    assert suc.justificativa_hash  # hash gravado
    # texto cru NUNCA na coluna:
    assert "celula de carga" not in suc.justificativa_hash


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_evento_sucateado_payload_sanitizado(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "Equipamento perdeu rastreabilidade do padrao primario."},
        format="json",
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        eventos = [
            e
            for e in Auditoria.objects.filter(action="equipamento.sucateado")
            if e.payload_jsonb.get("equipamento_id")
            == str(cenario["eq_sem_cert"].id)
        ]
    assert len(eventos) == 1
    payload_str = str(eventos[0].payload_jsonb)
    assert "padrao primario" not in payload_str
    assert str(cenario["cliente"].id) not in payload_str
    assert eventos[0].payload_jsonb["tem_cert_vigente_no_momento"] is False
    assert eventos[0].payload_jsonb["justificativa_hash"]


# ====================================================================
# T-EQP-043 — sucatar com cert vigente (P-EQP-S9)
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_sucatar_com_cert_sem_confirmacao_422(cenario):
    """Cert vigente sem confirmacao_dupla -> 422 com texto modal."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_com_cert'].id}/sucatear/",
        {
            "justificativa": (
                "Cliente desistiu do equipamento por troca tecnologica."
            ),
            "confirmacao_dupla": False,
        },
        format="json",
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["codigo"] == "cert_vigente_exige_confirmacao_dupla"
    assert body["texto_modal_versao_id"] == TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA
    # Modal texto canonico presente (sem composicao por LLM).
    assert "ISO/IEC 17025 §7.1.1" in body["texto_modal"]


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_sucatar_com_cert_sem_ciencia_validade_422(cenario):
    """Cert vigente com confirmacao_dupla mas SEM ciencia_validade -> 422."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_com_cert'].id}/sucatear/",
        {
            "justificativa": (
                "Cliente desistiu do equipamento por troca tecnologica."
            ),
            "confirmacao_dupla": True,
            "ciencia_validade_tecnica_registrada": False,
        },
        format="json",
    )
    assert resp.status_code == 422


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_sucatar_com_cert_happy_publica_evento_extra(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_com_cert'].id}/sucatear/",
        {
            "justificativa": (
                "Cliente desistiu apos troca de fornecedor; equipamento "
                "removido fisicamente do laboratorio."
            ),
            "confirmacao_dupla": True,
            "ciencia_validade_tecnica_registrada": True,
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["tem_cert_vigente_no_momento"] is True
    # Dois eventos publicados: sucateado + sucateado_com_cert_vigente.
    with run_in_tenant_context(cenario["tenant_a"].id):
        base = [
            e
            for e in Auditoria.objects.filter(action="equipamento.sucateado")
            if e.payload_jsonb.get("equipamento_id")
            == str(cenario["eq_com_cert"].id)
        ]
        extra = [
            e
            for e in Auditoria.objects.filter(
                action="equipamento.sucateado_com_cert_vigente"
            )
            if e.payload_jsonb.get("equipamento_id")
            == str(cenario["eq_com_cert"].id)
        ]
    assert len(base) == 1
    assert len(extra) == 1
    assert extra[0].payload_jsonb["ciencia_validade_tecnica_registrada"] is True
    assert (
        extra[0].payload_jsonb["texto_modal_versao_id"]
        == TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA
    )


# ====================================================================
# AC-EQP-005-3 — transicao terminal (regressao do migration 0002)
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_status_sucata_to_ativo_bloqueado_trigger(cenario):
    """Apos sucatear, UPDATE direto sucata->ativo deve falhar."""
    from django.db import connection

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "Equipamento perdeu rastreabilidade do padrao primario."},
        format="json",
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE equipamentos SET status='ativo' WHERE id=%s",
                    [str(cenario["eq_sem_cert"].id)],
                )
        except Exception as exc:
            msg = str(exc)
        else:
            msg = ""
    assert "transicao" in msg.lower() or "transicão" in msg.lower() or msg != ""


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_status_sucata_to_extraviado_permitido(cenario):
    """Apos sucatear, sucata->extraviado deve passar (excecao unica)."""
    from django.db import connection

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "Equipamento perdeu rastreabilidade do padrao primario."},
        format="json",
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE equipamentos SET status='extraviado' WHERE id=%s",
                [str(cenario["eq_sem_cert"].id)],
            )
        cenario["eq_sem_cert"].refresh_from_db()
    assert cenario["eq_sem_cert"].status == "extraviado"


# ====================================================================
# Validacoes & authz
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_justificativa_curta_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "curto"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_justificativa_com_pii_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {
            "justificativa": (
                "Sucateamos por solicitacao de Maria Santos da Costa via email."
            ),
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_perfil_sem_authz_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["leitor_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "Equipamento perdeu rastreabilidade do padrao primario."},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_sucatamento_duplicado_409(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "Equipamento perdeu rastreabilidade do padrao primario."},
        format="json",
    )
    assert r1.status_code == 200
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r2 = client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "Tentativa duplicada apos sucatamento ja efetivado."},
        format="json",
    )
    assert r2.status_code == 409


# ====================================================================
# T-EQP-045 — anti-drift do texto canonico
# ====================================================================


def test_texto_modal_versao_canonica_helper():
    """`texto_modal_sucatamento_cert_vigente` retorna texto canonico
    completo da versao atual."""
    texto = texto_modal_sucatamento_cert_vigente()
    assert "ISO/IEC 17025 §7.1.1" in texto
    assert "TECNICAMENTE VALIDO" in texto
    assert "TERMINAL" in texto
    # Versao desconhecida -> ValueError fail-loud.
    import pytest as _pt

    with _pt.raises(ValueError):
        texto_modal_sucatamento_cert_vigente("v9.99-2030-12-31")


def test_texto_modal_constante_versao_canonica_bate_doc():
    """Anti-drift: constante de versao = frontmatter do doc."""
    from pathlib import Path

    doc = Path("docs/conformidade/equipamentos/template-notificacao-sucatamento.md")
    assert doc.exists(), f"Doc canônico esperado em {doc}"
    conteudo = doc.read_text(encoding="utf-8")
    assert TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA in conteudo


# ====================================================================
# Trigger PG imutabilidade pos-INSERT
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_sucatamento_update_bloqueado_trigger(cenario):
    """UPDATE direto no registro de sucatamento bloqueado pelo trigger."""
    from django.db import connection

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "Equipamento perdeu rastreabilidade do padrao primario."},
        format="json",
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        suc = EquipamentoSucatamento.objects.get(
            equipamento_id=cenario["eq_sem_cert"].id
        )
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE equipamentos_sucatamento "
                    "SET texto_modal_versao_id='v9.99-2030-12-31' WHERE id=%s",
                    [str(suc.id)],
                )
        except Exception as exc:
            msg = str(exc)
        else:
            msg = ""
    assert "imutavel pos-INSERT" in msg or "T-EQP-042" in msg


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rls_sucatamento_cross_tenant_invisivel(cenario, db):
    """Sucatamento gravado em tenant_a invisivel em tenant_b."""
    sfx = uuid4().hex[:6]
    tenant_b = TenantFactory(slug=f"suc-b-{sfx}")
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    client.post(
        f"/api/v1/equipamentos/{cenario['eq_sem_cert'].id}/sucatear/",
        {"justificativa": "Equipamento perdeu rastreabilidade do padrao primario."},
        format="json",
    )
    with run_in_tenant_context(tenant_b.id):
        visiveis = EquipamentoSucatamento.objects.count()
    assert visiveis == 0


# ====================================================================
# Sanity texto modal constante completo
# ====================================================================


def test_texto_modal_constante_completa_4_paragrafos():
    """Texto canonico tem os 4 paragrafos exigidos pelo doc + checkboxes."""
    assert TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE.count("\n\n") >= 3
    assert "permanece TECNICAMENTE VALIDO" in TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE
    assert "Sucatamento e uma decisao OPERACIONAL" in TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE
    assert "LGPD art. 5º IX" in TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE
    assert "estado TERMINAL" in TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE
