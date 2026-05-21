"""Conserto ALTO-1 do Auditor de Segurança P5 (2026-05-21).

Trigger PG `trg_clientes_grava_op_tratamento` agora usa função
`pii_hash_hmac(text, uuid)` em vez de `sha256(...)` cru. O hash
gravado em `operacao_tratamento_cliente.payload->documento_hash`
deve casar exatamente com `hashear_pii_com_salt_tenant(documento,
tenant_id)` em Python — mesma chave HMAC, mesma mensagem.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from django.db import connection
from src.infrastructure.audit.models import OperacaoTratamentoCliente
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


@pytest.fixture
def tenant(db):
    return TenantFactory(slug=f"sec1-{uuid4().hex[:8]}")


@pytest.mark.django_db(transaction=True)
def test_trigger_documento_hash_eh_hmac_compatible_com_python(tenant):
    """SANEA-02 — hash gravado pelo trigger PG ≡ hashear_pii_com_salt_tenant Python."""
    documento = "11222333000181"
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento=documento,
            nome="HMAC Trigger Test",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        op = OperacaoTratamentoCliente.objects.filter(cliente_id=cliente.id).first()

    assert op is not None
    payload = op.payload if isinstance(op.payload, dict) else json.loads(op.payload)
    hash_gravado = payload["documento_hash"]
    hash_python = hashear_pii_com_salt_tenant(documento, tenant.id)
    assert (
        hash_gravado == hash_python
    ), f"Hash do trigger PG diverge do Python: PG={hash_gravado!r} vs Python={hash_python!r}"
    # Sanity: hash deve carregar prefixo de versão de chave (FA-A1).
    key_id, _, digest_hex = hash_gravado.partition(":")
    assert key_id, "hash sem prefixo de versão (FA-A1)"
    assert len(digest_hex) == 64, "digest SHA-256 hex deve ter 64 chars"


@pytest.mark.django_db(transaction=True)
def test_trigger_documento_hash_eh_distinto_entre_tenants(tenant):
    """Hash do mesmo documento em tenants diferentes deve diferir (defesa anti-correlação)."""
    documento = "11222333000181"
    tenant_b = TenantFactory(slug=f"sec1b-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant.id):
        ca = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento=documento,
            nome="Cliente Tenant A",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        op_a = OperacaoTratamentoCliente.objects.filter(cliente_id=ca.id).first()
    with run_in_tenant_context(tenant_b.id):
        cb = Cliente.objects.create(
            tenant=tenant_b,
            tipo_pessoa=TipoPessoa.PJ,
            documento=documento,
            nome="Cliente Tenant B",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        op_b = OperacaoTratamentoCliente.objects.filter(cliente_id=cb.id).first()
    assert op_a is not None and op_b is not None
    pa = op_a.payload if isinstance(op_a.payload, dict) else json.loads(op_a.payload)
    pb = op_b.payload if isinstance(op_b.payload, dict) else json.loads(op_b.payload)
    assert (
        pa["documento_hash"] != pb["documento_hash"]
    ), "Hash idêntico cross-tenant — correlação possível (SANEA-02)"


@pytest.mark.django_db(transaction=True)
def test_funcao_pii_hash_hmac_levanta_sem_chave_no_contexto(tenant):
    """Função PG `pii_hash_hmac` falha fail-loud se chave ausente — não retorna hash inseguro silencioso."""
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            # Apaga as GUCs de chave no contexto e tenta calcular o hash.
            cur.execute("SELECT set_config('app.pii_hash_key_ativa', '', true);")
            cur.execute("SELECT set_config('app.pii_hash_key_ativa_id', '', true);")
            with pytest.raises(Exception) as exc:
                cur.execute("SELECT pii_hash_hmac('11144477735', %s::uuid)", [str(tenant.id)])
                cur.fetchone()
    assert (
        "pii_hash_key_ativa" in str(exc.value)
        or "SANEA-02" in str(exc.value)
        or "fail-loud" in str(exc.value)
    )
