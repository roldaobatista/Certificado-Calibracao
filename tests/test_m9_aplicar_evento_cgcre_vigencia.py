"""M9 Fatia 1c (T-LIC-032) — testes PG da função `aplicar_evento_cgcre` estendida.

A migration tenant/0012 (D-LIC-2/3) adicionou `p_acreditacao_vigencia_fim` + a direção
`renovacao_vigencia_cgcre`. Prova que a vigência é GRAVADA no cache `Tenant.acreditacao_
vigencia_fim` (que o M8 lê) — fechando o mecanismo de sincronização (TL-M9-01). PG-real.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from django.db import DatabaseError, connection
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

_MOTIVO = "renovacao anual da acreditacao CGCRE conforme cronograma de supervisao do laboratorio acreditado " + "x" * 20


def _renovar(tenant_id, *, perfil_novo: str = "A", vigencia_fim=None) -> None:
    # run_in_tenant_context seta app.active_tenant_id — exigido pela RLS de bus_outbox
    # caso a direção emita evento (renovacao não emite, mas mantém o padrão consistente).
    with run_in_tenant_context(tenant_id), connection.cursor() as cur:
        cur.execute(
            "SELECT aplicar_evento_cgcre("
            "p_direcao => %s, p_tenant_id => %s, p_perfil_novo => %s, "
            "p_motivo => %s, p_acreditacao_vigencia_fim => %s)",
            ["renovacao_vigencia_cgcre", str(tenant_id), perfil_novo, _MOTIVO, vigencia_fim],
        )


@pytest.mark.django_db
def test_renovacao_seta_vigencia_fim_sem_mudar_perfil() -> None:
    tenant = TenantFactory(perfil_a=True)
    nova = date(2028, 12, 31)
    _renovar(tenant.id, vigencia_fim=nova)
    tenant.refresh_from_db()
    assert tenant.perfil_regulatorio == "A"
    assert tenant.acreditacao_vigencia_fim == nova


@pytest.mark.django_db
def test_renovacao_perfil_b_rejeitada() -> None:
    tenant = TenantFactory(perfil_b=True)
    with pytest.raises(DatabaseError, match="renovacao_vigencia_cgcre so se aplica a perfil A"):
        _renovar(tenant.id, perfil_novo="B", vigencia_fim=date(2028, 1, 1))


@pytest.mark.django_db
def test_renovacao_sem_vigencia_fim_rejeitada() -> None:
    tenant = TenantFactory(perfil_a=True)
    with pytest.raises(DatabaseError, match="exige p_acreditacao_vigencia_fim"):
        _renovar(tenant.id, vigencia_fim=None)


@pytest.mark.django_db
def test_backward_compat_chamada_sem_vigencia_ainda_funciona() -> None:
    # Suspensão (caminho legado, sem param de vigência) — a função de 14 params
    # aceita chamadas que não passam o 14º (default NULL). Backward-compat (D-LIC-2).
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id), connection.cursor() as cur:
        cur.execute(
            "SELECT aplicar_evento_cgcre("
            "p_direcao => %s, p_tenant_id => %s, p_perfil_novo => %s, p_motivo => %s, "
            "p_documento_cgcre_id => %s, p_suspensa_em => %s, p_suspensa_ate => %s)",
            ["suspensao_temporaria_cgcre", str(tenant.id), "A", _MOTIVO,
             str(uuid4()), date(2026, 7, 1), date(2026, 9, 1)],
        )
    tenant.refresh_from_db()
    assert tenant.perfil_regulatorio == "A"
    assert tenant.acreditacao_suspensa_em == date(2026, 7, 1)
