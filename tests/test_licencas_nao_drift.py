"""M9 Fatia 3 (T-LIC-052) — invariante de NÃO-DRIFT `cache == fonte` + reverde M8.

ADR-0079: `Licenca`(ACREDITACAO_CGCRE) é a FONTE rica; `Tenant.acreditacao_vigencia_fim`
é CACHE desnormalizado sincronizado UNIDIRECIONALMENTE via `aplicar_evento_cgcre`
(nunca UPDATE direto). Este teste prova end-to-end (PG-real) que, após a promoção e a
renovação, o cache continua IGUAL à fonte (`vigencia_fim_acreditacao_cgcre`) — fecha
**GATE-CER-CGCRE-VIG-DATA-POPULAR + GATE-LIC-DRIFT**.

Reverde M8: com o cache populado, `acreditacao_vigente_para_rbc` (transição do M8) sai
do fail-open lazy (`None=True`) e REBAIXA real RBC→não-RBC quando a vigência venceu na
data de emissão.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.domain.metrologia.certificados.transicoes import acreditacao_vigente_para_rbc
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.metrologia.licencas_acreditacoes.query_service import (
    vigencia_fim_acreditacao_cgcre,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory
from tests.test_m9_licencas_api_p2 import _autenticar, _post

_DBS = ["default", "breaker_writer"]


def _cenario_b():
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"lic-drift-{sfx}", perfil_b=True)
    admin = UsuarioFactory(email=f"adm-drift-{sfx}@lic.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return tenant, admin


def _cache_fim(tenant):
    tenant.refresh_from_db()
    return tenant.acreditacao_vigencia_fim


def _fonte_fim(tenant):
    with run_in_tenant_context(tenant.id):
        return vigencia_fim_acreditacao_cgcre(tenant_id=tenant.id)


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cache_igual_fonte_apos_promover_e_renovar():
    tenant, admin = _cenario_b()
    client = APIClient()
    _autenticar(client, admin, tenant)

    # 1. Promove B→A: cache populado pela função; fonte = a Licenca cadastrada.
    r = _post(
        client, "/api/v1/licencas/promover-perfil-a/",
        {
            "perfil_novo": "A", "numero": "CRL-DRIFT", "orgao_emissor": "CGCRE",
            "vigencia_inicio": "2026-01-01", "vigencia_fim": "2030-12-31",
            "escopo": "massa 0..10kg", "numero_cgcre": "CRL-DRIFT",
            "assinatura_a3_id": str(uuid4()),
            "motivo": "promocao a perfil A apos auditoria CGCRE concluida " + "y" * 50,
            "auditor_cgcre": "Auditor Fulano", "anexo_id": str(uuid4()),
            "anexo_sha256": "b" * 64, "correlation_id": str(uuid4()),
        },
    )
    assert r.status_code == 201, r.content
    doc_id = r.json()["id"]
    assert _cache_fim(tenant) == date(2030, 12, 31)
    assert _cache_fim(tenant) == _fonte_fim(tenant)  # cache == fonte

    # 2. Renova a acreditação CGCRE (tenant A): a renovação sincroniza o cache.
    rr = _post(
        client, f"/api/v1/licencas/{doc_id}/renovar/",
        {
            "nova_vigencia_inicio": "2031-01-01", "nova_vigencia_fim": "2035-12-31",
            "anexo_id": str(uuid4()), "anexo_sha256": "c" * 64,
            "motivo": "RENOVACAO", "correlation_id": str(uuid4()),
        },
    )
    assert rr.status_code == 201, rr.content
    assert _cache_fim(tenant) == date(2035, 12, 31)
    assert _cache_fim(tenant) == _fonte_fim(tenant)  # cache continua == fonte


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_reverde_m8_cache_populado_rebaixa_real():
    tenant, admin = _cenario_b()
    client = APIClient()
    _autenticar(client, admin, tenant)
    _post(
        client, "/api/v1/licencas/promover-perfil-a/",
        {
            "perfil_novo": "A", "numero": "CRL-M8", "orgao_emissor": "CGCRE",
            "vigencia_inicio": "2026-01-01", "vigencia_fim": "2030-12-31",
            "escopo": "massa 0..10kg", "numero_cgcre": "CRL-M8",
            "assinatura_a3_id": str(uuid4()),
            "motivo": "promocao a perfil A apos auditoria CGCRE concluida " + "y" * 50,
            "auditor_cgcre": "Auditor Fulano", "anexo_id": str(uuid4()),
            "anexo_sha256": "b" * 64, "correlation_id": str(uuid4()),
        },
    )
    cache = _cache_fim(tenant)
    assert cache == date(2030, 12, 31)

    # Emissão DENTRO da vigência → RBC ainda OK.
    assert acreditacao_vigente_para_rbc(
        perfil="A", acreditacao_vigencia_fim=cache,
        acreditacao_suspensa_em=None, acreditacao_suspensa_ate=None,
        data_emissao=date(2030, 6, 1),
    ) is True
    # Emissão APÓS o vencimento → rebaixa real (sai do fail-open None=True).
    assert acreditacao_vigente_para_rbc(
        perfil="A", acreditacao_vigencia_fim=cache,
        acreditacao_suspensa_em=None, acreditacao_suspensa_ate=None,
        data_emissao=date(2031, 6, 1),
    ) is False
