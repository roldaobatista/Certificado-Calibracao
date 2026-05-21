"""T-CLI-111 + T-CLI-112 (US-CLI-005) — dedup compare + mesclagem completa.

T-CLI-111 (AC-CLI-005-1):
1. test_dedup_compare_retorna_campos_lado_a_lado
2. test_dedup_compare_404_se_vencedor_nao_existe
3. test_dedup_compare_404_se_perdedor_nao_existe
4. test_dedup_compare_403_tenants_diferentes
5. test_dedup_compare_contagens_wave_a_gate

T-CLI-112 (AC-CLI-005-3b):
6. test_mesclar_rejeita_400_tipo_invalido
7. test_mesclar_rejeita_400_ma_sem_evidencia
8. test_mesclar_aceita_DUPLICATA_OPERACIONAL_sem_evidencia
9. test_mesclar_aceita_MA_SOCIETARIO_com_evidencia
10. test_mesclar_audit_payload_inclui_tipo_e_evidencia
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import connection
from src.infrastructure.clientes.models import Cliente
from src.infrastructure.multitenant.connection import (
    run_in_tenant_context,
)

from tests.factories import TenantFactory


def _criar_cliente(tenant, documento, nome="Foo Bar") -> Cliente:
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa="PF",
        documento=documento,
        nome=nome,
        aceite_lgpd_em="2026-05-20T10:00:00Z",
        aceite_lgpd_versao="v1",
        aceite_lgpd_origem="CADASTRO_DIRETO",
        aceite_lgpd_base_legal="EXECUCAO_CONTRATO",
    )


# =============================================================
# T-CLI-111 — dedup compare
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_dedup_compare_retorna_campos_lado_a_lado():
    from src.infrastructure.clientes.views import ClienteViewSet

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        v = _criar_cliente(tenant, "11144477735", nome="João Silva")
        p = _criar_cliente(tenant, "52998224725", nome="João S.")
    # Chamada direta ao método (sem subir o middleware completo aqui)
    from rest_framework.test import APIRequestFactory

    factory = APIRequestFactory()
    request = factory.get(f"/api/v1/clientes/{v.id}/dedup/{p.id}/")
    view = ClienteViewSet()
    view.request = request
    view.kwargs = {"pk": str(v.id), "perdedor_id": str(p.id)}
    with run_in_tenant_context(tenant.id):
        resp = view.dedup_compare(request, pk=str(v.id), perdedor_id=str(p.id))
    assert resp.status_code == 200
    campos = {c["campo"]: c for c in resp.data["campos"]}
    assert campos["nome"]["vencedor"] == "João Silva"
    assert campos["nome"]["perdedor"] == "João S."


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_dedup_compare_404_se_vencedor_nao_existe():
    from rest_framework.test import APIRequestFactory
    from src.infrastructure.clientes.views import ClienteViewSet

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        p = _criar_cliente(tenant, "11144477735")
    factory = APIRequestFactory()
    pk_falso = uuid4()
    request = factory.get(f"/api/v1/clientes/{pk_falso}/dedup/{p.id}/")
    view = ClienteViewSet()
    view.request = request
    with run_in_tenant_context(tenant.id):
        resp = view.dedup_compare(request, pk=str(pk_falso), perdedor_id=str(p.id))
    assert resp.status_code == 404
    assert resp.data["detail"] == "vencedor_nao_encontrado"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_dedup_compare_404_se_perdedor_nao_existe():
    from rest_framework.test import APIRequestFactory
    from src.infrastructure.clientes.views import ClienteViewSet

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        v = _criar_cliente(tenant, "11144477735")
    perdedor_falso = uuid4()
    factory = APIRequestFactory()
    request = factory.get(f"/api/v1/clientes/{v.id}/dedup/{perdedor_falso}/")
    view = ClienteViewSet()
    view.request = request
    with run_in_tenant_context(tenant.id):
        resp = view.dedup_compare(request, pk=str(v.id), perdedor_id=str(perdedor_falso))
    assert resp.status_code == 404
    assert resp.data["detail"] == "perdedor_nao_encontrado"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_dedup_compare_contagens_wave_a_gate():
    """Contagens são 0 em Marco 1 (módulos OS/cert/fatura/contatos Wave A)."""
    from rest_framework.test import APIRequestFactory
    from src.infrastructure.clientes.views import ClienteViewSet

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        v = _criar_cliente(tenant, "11144477735")
        p = _criar_cliente(tenant, "52998224725")
    factory = APIRequestFactory()
    request = factory.get(f"/api/v1/clientes/{v.id}/dedup/{p.id}/")
    view = ClienteViewSet()
    view.request = request
    with run_in_tenant_context(tenant.id):
        resp = view.dedup_compare(request, pk=str(v.id), perdedor_id=str(p.id))
    assert resp.data["contagens"]["os_atreladas"] == {"vencedor": 0, "perdedor": 0}
    assert resp.data["contagens"]["certificados_atrelados"] == {
        "vencedor": 0,
        "perdedor": 0,
    }
    assert "gate_wave_a" in resp.data


# =============================================================
# T-CLI-112 — tipo_mesclagem + evidencia_documental_id
# =============================================================


def _build_mesclar_request(payload, *, vencedor_id, perdedor_id):
    """Helper: chama o método mesclar diretamente com payload (DRF Request)."""
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request
    from rest_framework.test import APIRequestFactory
    from src.infrastructure.clientes.views import ClienteViewSet

    factory = APIRequestFactory()
    wsgi_request = factory.post(
        f"/api/v1/clientes/{vencedor_id}/mesclar/{perdedor_id}",
        payload,
        format="json",
    )
    request = Request(wsgi_request, parsers=[JSONParser()])
    view = ClienteViewSet()
    view.request = request
    return view, request


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_mesclar_rejeita_400_tipo_invalido():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        v = _criar_cliente(tenant, "11144477735")
        p = _criar_cliente(tenant, "52998224725")
        view, request = _build_mesclar_request(
            {
                "motivo_categoria": "duplicacao_atendimento",
                "tipo_mesclagem": "INVALIDO_XYZ",
            },
            vencedor_id=v.id,
            perdedor_id=p.id,
        )
        resp = view.mesclar(request, pk=str(v.id), perdedor_id=str(p.id))
    assert resp.status_code == 400
    assert resp.data["detail"] == "tipo_mesclagem_invalido"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_mesclar_rejeita_400_ma_sem_evidencia():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        v = _criar_cliente(tenant, "11144477735")
        p = _criar_cliente(tenant, "52998224725")
        view, request = _build_mesclar_request(
            {
                "motivo_categoria": "duplicacao_atendimento",
                "tipo_mesclagem": "M&A_SOCIETARIO",
                # sem evidencia_documental_id
            },
            vencedor_id=v.id,
            perdedor_id=p.id,
        )
        resp = view.mesclar(request, pk=str(v.id), perdedor_id=str(p.id))
    assert resp.status_code == 400
    assert resp.data["detail"] == "evidencia_documental_obrigatoria_em_ma"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_mesclar_aceita_DUPLICATA_OPERACIONAL_sem_evidencia():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        v = _criar_cliente(tenant, "11144477735")
        p = _criar_cliente(tenant, "52998224725")
        view, request = _build_mesclar_request(
            {
                "motivo_categoria": "duplicacao_atendimento",
                "tipo_mesclagem": "DUPLICATA_OPERACIONAL",
            },
            vencedor_id=v.id,
            perdedor_id=p.id,
        )
        resp = view.mesclar(request, pk=str(v.id), perdedor_id=str(p.id))
    assert resp.status_code == 200
    assert resp.data["vencedor_id"] == str(v.id)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_mesclar_aceita_MA_SOCIETARIO_com_evidencia():
    tenant = TenantFactory()
    evid = str(uuid4())
    with run_in_tenant_context(tenant.id):
        v = _criar_cliente(tenant, "11144477735")
        p = _criar_cliente(tenant, "52998224725")
        view, request = _build_mesclar_request(
            {
                "motivo_categoria": "reorganizacao_societaria",
                "tipo_mesclagem": "M&A_SOCIETARIO",
                "evidencia_documental_id": evid,
            },
            vencedor_id=v.id,
            perdedor_id=p.id,
        )
        resp = view.mesclar(request, pk=str(v.id), perdedor_id=str(p.id))
    assert resp.status_code == 200


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_mesclar_audit_payload_inclui_tipo_e_evidencia():
    """Evento `cliente.mesclado` carrega tipo_mesclagem + evidencia_documental_id."""
    tenant = TenantFactory()
    evid = str(uuid4())
    with run_in_tenant_context(tenant.id):
        v = _criar_cliente(tenant, "11144477735")
        p = _criar_cliente(tenant, "52998224725")
        view, request = _build_mesclar_request(
            {
                "motivo_categoria": "reorganizacao_societaria",
                "tipo_mesclagem": "M&A_SOCIETARIO",
                "evidencia_documental_id": evid,
            },
            vencedor_id=v.id,
            perdedor_id=p.id,
        )
        view.mesclar(request, pk=str(v.id), perdedor_id=str(p.id))
        # Lê o evento na cadeia F-A
        with connection.cursor() as cur:
            cur.execute(
                "SELECT payload_jsonb FROM auditoria "
                "WHERE action = 'cliente.mesclado' "
                "AND payload_jsonb->>'vencedor_id' = %s",
                [str(v.id)],
            )
            row = cur.fetchone()
    assert row is not None
    import json as _json

    payload_raw = row[0]
    payload = payload_raw if isinstance(payload_raw, dict) else _json.loads(payload_raw)
    assert payload["tipo_mesclagem"] == "M&A_SOCIETARIO"
    assert payload["evidencia_documental_id"] == evid
