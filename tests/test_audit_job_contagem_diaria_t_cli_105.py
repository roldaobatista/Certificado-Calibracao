"""T-CLI-105 / INV-013-A — testes do job daily de contagem de
AcessoDadosCliente.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.audit.services import registrar_acesso_dados_cliente
from src.infrastructure.multitenant.connection import run_as_system, run_in_tenant_context

from tests.factories import TenantFactory


@pytest.mark.django_db(transaction=True)
def test_job_grava_contagem_para_cada_tenant_ativo():
    """AcessoDadosCliente é INSERT-only (trigger anti-mutation impede setar
    timestamp histórico). Estratégia: rodar acessos AGORA e contar HOJE."""
    hoje = datetime.now(UTC).date()
    t1 = TenantFactory()
    t2 = TenantFactory()

    with run_in_tenant_context(t1.id):
        for _ in range(3):
            registrar_acesso_dados_cliente(
                tenant_id=t1.id,
                usuario_id=None,
                cliente_id=None,
                finalidade="atendimento_pos_venda",
            )
    with run_in_tenant_context(t2.id):
        registrar_acesso_dados_cliente(
            tenant_id=t2.id,
            usuario_id=None,
            cliente_id=None,
            finalidade="atendimento_pos_venda",
        )

    out = StringIO()
    call_command(
        "job_contagem_diaria_acesso_pii",
        f"--data-referencia={hoje.isoformat()}",
        stdout=out,
    )
    saida = out.getvalue()
    assert f"tenant={t1.id}" in saida
    assert f"tenant={t2.id}" in saida
    assert "Total" in saida

    # 2 linhas na cadeia sistema (1 por tenant) com action correta
    with run_as_system():
        eventos = list(
            Auditoria.objects.filter(
                action="acessos_pii.contagem_diaria",
                resource_summary__contains=hoje.isoformat(),
            )
        )
    actions_t1 = [e for e in eventos if str(t1.id) in e.resource_summary]
    actions_t2 = [e for e in eventos if str(t2.id) in e.resource_summary]
    assert len(actions_t1) == 1
    assert len(actions_t2) == 1
    assert actions_t1[0].payload_jsonb["qtd"] == 3
    assert actions_t2[0].payload_jsonb["qtd"] == 1


@pytest.mark.django_db(transaction=True)
def test_job_data_referencia_padrao_ontem():
    """Sem --data-referencia, default = D-1."""
    TenantFactory()
    out = StringIO()
    call_command("job_contagem_diaria_acesso_pii", stdout=out)
    saida = out.getvalue()
    ontem = (datetime.now(UTC) - timedelta(days=1)).date()
    assert ontem.isoformat() in saida


@pytest.mark.django_db(transaction=True)
def test_job_data_referencia_invalida_falha():
    from django.core.management.base import CommandError

    with pytest.raises(CommandError, match="data-referencia"):
        call_command("job_contagem_diaria_acesso_pii", "--data-referencia=banana")
