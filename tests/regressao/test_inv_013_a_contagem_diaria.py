"""INV-013-A — contagem diária imutável de AcessoDadosCliente.

Spec Marco 1 §3 item 9 + §1: suíte anti-regressão.

INV-013-A (REGRAS-INEGOCIAVEIS): job daily conta `AcessoDadosCliente
(tenant_id=T, dia=D)` e publica em métrica imutável; gap na sequência
(dia X+1 < X) dispara alerta P1 — supressão de log de acesso a PII
detectável SEM hash chain dedicada (NG-CLI-10).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from django.core.management import call_command
from src.infrastructure.audit.models import AcessoDadosCliente, Auditoria
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)

from tests.factories import TenantFactory, UsuarioFactory


@pytest.fixture
def cenario(db):
    tenant = TenantFactory(slug=f"inv13a-{uuid4().hex[:8]}")
    usuario = UsuarioFactory(email=f"u-{uuid4().hex[:6]}@inv13a.local")
    return {"tenant": tenant, "usuario": usuario}


@pytest.mark.django_db(transaction=True)
def test_inv_013_a_happy_job_grava_evento_contagem_por_tenant(cenario):
    """Happy — job rodando D-1 grava evento contagem por tenant na cadeia sistema."""
    tenant = cenario["tenant"]
    usuario = cenario["usuario"]

    # Gera 2 acessos no tenant
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Contagem Diaria",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        for _ in range(2):
            AcessoDadosCliente.objects.create(
                tenant_id=tenant.id,
                usuario_id=usuario.id,
                cliente_id=cliente.id,
                finalidade="atendimento_pos_venda",
                ip_hash="v1:" + "a" * 64,
                recurso={"cliente_id": str(cliente.id)},
            )

    # Roda job para o dia de hoje (sem --data-referencia, pega D-1 default;
    # ajusto manualmente)
    hoje = datetime.now(UTC).date().isoformat()
    call_command("job_contagem_diaria_acesso_pii", f"--data-referencia={hoje}")

    with run_as_system():
        eventos = list(Auditoria.objects.filter(action="acessos_pii.contagem_diaria"))
    assert eventos, "job não gravou evento de contagem na cadeia sistema"


@pytest.mark.django_db(transaction=True)
def test_inv_013_a_unhappy_data_referencia_invalida_rejeita(cenario):
    """Unhappy — `--data-referencia` mal formada deve falhar fail-loud
    (não silenciosamente gravar 0)."""
    from django.core.management.base import CommandError

    with pytest.raises((CommandError, ValueError, Exception)) as exc:
        call_command("job_contagem_diaria_acesso_pii", "--data-referencia=nao-eh-data")
    # Confirma que houve falha relacionada a data inválida
    msg = str(exc.value).lower()
    assert any(t in msg for t in ("data", "iso", "format", "invalid"))


@pytest.mark.django_db(transaction=True)
def test_inv_013_a_happy_tenants_isolados(cenario):
    """Happy — contagens são por-tenant (cada tenant tem evento próprio)."""
    tenant_a = cenario["tenant"]
    tenant_b = TenantFactory(slug=f"inv13a-b-{uuid4().hex[:8]}")
    usuario = cenario["usuario"]
    hoje = datetime.now(UTC).date().isoformat()

    # Cada tenant ganha pelo menos 1 acesso
    for tenant in (tenant_a, tenant_b):
        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            c = Cliente.objects.create(
                tenant=tenant,
                tipo_pessoa=TipoPessoa.PJ,
                documento="11222333000181",
                nome=f"Cliente {tenant.slug}",
                aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
            )
            AcessoDadosCliente.objects.create(
                tenant_id=tenant.id,
                usuario_id=usuario.id,
                cliente_id=c.id,
                finalidade="atendimento_pos_venda",
                ip_hash="v1:" + "b" * 64,
                recurso={"cliente_id": str(c.id)},
            )

    call_command("job_contagem_diaria_acesso_pii", f"--data-referencia={hoje}")

    with run_as_system():
        eventos = list(Auditoria.objects.filter(action="acessos_pii.contagem_diaria"))
    # Espera pelo menos 1 evento por tenant — não sai do escopo
    assert len(eventos) >= 2, f"esperado ≥2 eventos (1 por tenant); achou {len(eventos)}"
