"""Audit trail authz: imutavel + commit-before-response + hash chain (INV-AUTHZ-002)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from django.db.utils import InternalError, ProgrammingError
from src.infrastructure.authz.django_provider import (
    DjangoAuthorizationProvider,
    invalidate_user_cache,
)
from src.infrastructure.authz.models import AuthzDecision
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)


def _cenario(perfil_codigo: str):
    """Fixture-helper: 1 tenant + 1 usuario com perfil."""
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"tenant-imut-{suffix}")
    usuario = UsuarioFactory(email=f"{perfil_codigo}-{suffix}@imut.local")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant, perfil=perfil_codigo)
    invalidate_user_cache(usuario.id, tenant.id)
    return tenant, usuario


@pytest.mark.django_db(transaction=True)
def test_inv_authz_002_grava_audit_antes_de_retornar_allowed():
    """Decisao allowed grava AuthzDecision ANTES de retornar (sincrono)."""
    tenant, usuario = _cenario("admin_tenant")
    provider = DjangoAuthorizationProvider()

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        contagem_antes = AuthzDecision.objects.filter(tenant_id=tenant.id).count()
        decision = provider.can(
            usuario_id=usuario.id,
            action="os.criar",
            tenant_id=tenant.id,
            purpose="execucao_contrato",
        )
        assert decision.allowed is True
        assert decision.audit_id is not None
        # Linha existe ANTES do return — contagem aumentou de 1
        contagem_depois = AuthzDecision.objects.filter(tenant_id=tenant.id).count()
        assert contagem_depois == contagem_antes + 1
        linha = AuthzDecision.objects.get(id=decision.audit_id)
        assert linha.decision == "allowed"
        assert linha.action == "os.criar"
        assert linha.reason == "ok"


@pytest.mark.django_db(transaction=True)
def test_inv_authz_002_grava_audit_antes_de_retornar_denied():
    """Mesma garantia para decisao denied."""
    tenant, usuario = _cenario("tecnico")
    provider = DjangoAuthorizationProvider()

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        decision = provider.can(
            usuario_id=usuario.id,
            action="fatura.estornar",
            tenant_id=tenant.id,
        )
        assert decision.allowed is False
        assert decision.audit_id is not None
        linha = AuthzDecision.objects.get(id=decision.audit_id)
        assert linha.decision == "denied"
        assert linha.reason == "rbac_denied"


@pytest.mark.django_db(transaction=True)
def test_inv_authz_002_trigger_pg_bloqueia_update():
    """UPDATE direto em authz_decisions e BLOQUEADO pelo trigger PG."""
    tenant, usuario = _cenario("admin_tenant")
    provider = DjangoAuthorizationProvider()

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        decision = provider.can(
            usuario_id=usuario.id,
            action="os.criar",
            tenant_id=tenant.id,
        )
        linha = AuthzDecision.objects.get(id=decision.audit_id)
        with pytest.raises((IntegrityError, InternalError, ProgrammingError)):
            with transaction.atomic():
                linha.reason = "tampered"
                linha.save(update_fields=["reason"])


@pytest.mark.django_db(transaction=True)
def test_inv_authz_002_trigger_pg_bloqueia_delete():
    """DELETE direto em authz_decisions e BLOQUEADO pelo trigger PG."""
    tenant, usuario = _cenario("admin_tenant")
    provider = DjangoAuthorizationProvider()

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        decision = provider.can(
            usuario_id=usuario.id,
            action="os.criar",
            tenant_id=tenant.id,
        )
        linha = AuthzDecision.objects.get(id=decision.audit_id)
        with pytest.raises((IntegrityError, InternalError, ProgrammingError)):
            with transaction.atomic():
                linha.delete()


@pytest.mark.django_db(transaction=True)
def test_inv_authz_002_hash_chain_encadeia_linhas():
    """Cada linha tem hash_atual = sha256(hash_anterior || payload)."""
    tenant, usuario = _cenario("admin_tenant")
    provider = DjangoAuthorizationProvider()

    decisoes_ids = []
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        for _ in range(3):
            d = provider.can(
                usuario_id=usuario.id,
                action="os.criar",
                tenant_id=tenant.id,
            )
            decisoes_ids.append(d.audit_id)
        # FB-C1: ordena por `sequencia` (monotônica) — `timestamp` colide em
        # µs sob o advisory lock (era o bug; correção alinhada ao invariante).
        linhas = list(AuthzDecision.objects.filter(id__in=decisoes_ids).order_by("sequencia"))
    # Primeira linha do tenant pode ser a 1a do test_db ou nao;
    # garantimos apenas que cada hash_atual e diferente e hash_anterior
    # de linhas subsequentes bate com hash_atual anterior dentro da serie.
    assert len(linhas) == 3
    for i in range(1, 3):
        assert linhas[i].hash_anterior == linhas[i - 1].hash_atual
        assert linhas[i].hash_atual != linhas[i - 1].hash_atual
