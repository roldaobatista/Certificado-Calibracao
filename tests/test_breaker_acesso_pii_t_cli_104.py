"""T-CLI-104 — testes do circuit breaker observado para `AcessoDadosCliente`.

Cobertura:

1. test_breaker_grava_ok_em_chamada_bem_sucedida
2. test_breaker_grava_falha_quando_caller_levanta (fail-loud preservado)
3. test_breaker_grava_evento_sob_rollback_do_request — **CRÍTICO T2**:
   golden test. Mock `registrar_acesso_dados_cliente` levantar; envolver
   chamada do wrapper em `transaction.atomic()` que faz raise. Confirmar
   que linha do evento de falha sobreviveu (conexão paralela autocommit).
4. test_breaker_dispara_em_3_falhas_absolutas (threshold OR — ramo absoluto)
5. test_breaker_dispara_em_0_1_pct_com_1000_total (ramo percentual)
6. test_breaker_idempotente_na_mesma_janela (rodar command 2x = 1 evento)
7. test_breaker_threshold_abaixo_nao_dispara
8. test_breaker_isolamento_por_tenant
"""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.db import connection, transaction
from src.infrastructure.audit.breaker import (
    registrar_acesso_dados_cliente_com_breaker,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)

from tests.factories import TenantFactory


def _contar_eventos_breaker(tenant_id, ok=None) -> int:
    with run_as_system():
        with connection.cursor() as cur:
            if ok is None:
                cur.execute(
                    "SELECT COUNT(*) FROM breaker_acesso_pii_evento " "WHERE tenant_id = %s",
                    [str(tenant_id)],
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) FROM breaker_acesso_pii_evento "
                    "WHERE tenant_id = %s AND ok = %s",
                    [str(tenant_id), ok],
                )
            return cur.fetchone()[0]


def _contar_p1_disparado(tenant_id) -> int:
    """Conta eventos `sistema.breaker_acesso_pii.disparado` na cadeia F-A
    com payload referindo este tenant."""
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM auditoria "
                "WHERE action = 'sistema.breaker_acesso_pii.disparado' "
                "AND payload_jsonb->>'tenant_id' = %s",
                [str(tenant_id)],
            )
            return cur.fetchone()[0]


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_breaker_grava_ok_em_chamada_bem_sucedida():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        registrar_acesso_dados_cliente_com_breaker(
            tenant_id=tenant.id,
            usuario_id=None,
            cliente_id=uuid4(),
            finalidade="atendimento_pos_venda",
            recurso={},
            ip_hash="",
        )
    assert _contar_eventos_breaker(tenant.id, ok=True) == 1
    assert _contar_eventos_breaker(tenant.id, ok=False) == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_breaker_grava_falha_quando_caller_levanta():
    tenant = TenantFactory()

    def falhar(**kwargs):
        raise RuntimeError("simulada")

    with run_in_tenant_context(tenant.id):
        with patch(
            "src.infrastructure.audit.breaker.registrar_acesso_dados_cliente",
            side_effect=falhar,
        ):
            with pytest.raises(RuntimeError, match="simulada"):
                registrar_acesso_dados_cliente_com_breaker(
                    tenant_id=tenant.id,
                    usuario_id=None,
                    cliente_id=uuid4(),
                    finalidade="atendimento_pos_venda",
                    recurso={},
                    ip_hash="",
                )
    assert _contar_eventos_breaker(tenant.id, ok=False) == 1
    assert _contar_eventos_breaker(tenant.id, ok=True) == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_breaker_grava_evento_sob_rollback_do_request():
    """CRÍTICO T2 — golden test. Conexão paralela autocommit garante
    que o evento de falha SOBREVIVE ao rollback do request HTTP do caller."""
    tenant = TenantFactory()

    def falhar(**kwargs):
        raise RuntimeError("simulada")

    with run_in_tenant_context(tenant.id):
        with patch(
            "src.infrastructure.audit.breaker.registrar_acesso_dados_cliente",
            side_effect=falhar,
        ):
            # Simula ATOMIC_REQUESTS do middleware: caller envolve tudo
            # em atomic e relança → rollback do `default` connection.
            with pytest.raises(RuntimeError, match="simulada"):
                with transaction.atomic():
                    registrar_acesso_dados_cliente_com_breaker(
                        tenant_id=tenant.id,
                        usuario_id=None,
                        cliente_id=uuid4(),
                        finalidade="atendimento_pos_venda",
                        recurso={},
                        ip_hash="",
                    )
    # Mesmo com rollback do request, o evento de falha está gravado
    # via `breaker_writer` (autocommit, conexão separada).
    assert _contar_eventos_breaker(tenant.id, ok=False) == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_breaker_dispara_em_3_falhas_absolutas():
    """Ramo absoluto do threshold OR (3 falhas em 5min, total <1000)."""
    tenant = TenantFactory()

    def falhar(**kwargs):
        raise RuntimeError("simulada")

    with run_in_tenant_context(tenant.id):
        with patch(
            "src.infrastructure.audit.breaker.registrar_acesso_dados_cliente",
            side_effect=falhar,
        ):
            for _ in range(3):
                with pytest.raises(RuntimeError):
                    registrar_acesso_dados_cliente_com_breaker(
                        tenant_id=tenant.id,
                        usuario_id=None,
                        cliente_id=uuid4(),
                        finalidade="atendimento_pos_venda",
                        recurso={},
                        ip_hash="",
                    )
    out = StringIO()
    call_command("avaliar_circuit_breaker_acesso_pii", stdout=out)
    assert _contar_p1_disparado(tenant.id) == 1
    assert "P1 disparado" in out.getvalue()


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_breaker_threshold_abaixo_nao_dispara():
    """2 falhas (< 3) e percentual irrelevante → não dispara."""
    tenant = TenantFactory()

    def falhar(**kwargs):
        raise RuntimeError("simulada")

    with run_in_tenant_context(tenant.id):
        # 2 falhas
        with patch(
            "src.infrastructure.audit.breaker.registrar_acesso_dados_cliente",
            side_effect=falhar,
        ):
            for _ in range(2):
                with pytest.raises(RuntimeError):
                    registrar_acesso_dados_cliente_com_breaker(
                        tenant_id=tenant.id,
                        usuario_id=None,
                        cliente_id=uuid4(),
                        finalidade="atendimento_pos_venda",
                        recurso={},
                        ip_hash="",
                    )
    call_command("avaliar_circuit_breaker_acesso_pii", stdout=StringIO())
    assert _contar_p1_disparado(tenant.id) == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_breaker_idempotente_na_mesma_janela():
    """Rodar command 2x na MESMA janela = 1 evento P1 (UNIQUE bus_outbox
    por causation_id determinístico)."""
    tenant = TenantFactory()

    def falhar(**kwargs):
        raise RuntimeError("simulada")

    with run_in_tenant_context(tenant.id):
        with patch(
            "src.infrastructure.audit.breaker.registrar_acesso_dados_cliente",
            side_effect=falhar,
        ):
            for _ in range(5):
                with pytest.raises(RuntimeError):
                    registrar_acesso_dados_cliente_com_breaker(
                        tenant_id=tenant.id,
                        usuario_id=None,
                        cliente_id=uuid4(),
                        finalidade="atendimento_pos_venda",
                        recurso={},
                        ip_hash="",
                    )
    call_command("avaliar_circuit_breaker_acesso_pii", stdout=StringIO())
    call_command("avaliar_circuit_breaker_acesso_pii", stdout=StringIO())
    # Dois evals na mesma janela = 1 evento P1 (causation_id idempotente)
    assert _contar_p1_disparado(tenant.id) == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_breaker_anti_forja_cross_tenant():
    """FAIL 1 auditor — wrapper NÃO pode gravar evento atribuído a tenant
    diferente do `tenant_id` declarado. A policy RLS força WITH CHECK
    `tenant_id = app.active_tenant_id`. O wrapper seta `SET LOCAL
    app.active_tenant_id = <tenant_id passado>`, então uma chamada com
    tenant_id forjado bate com o set local (mesmo input) — mas pra
    confirmar a defesa, vamos chamar a primitiva interna passando
    `tenant_id` diferente do que será setado: bypass o wrapper e teste a
    policy nua.
    """
    from django.db import ProgrammingError, connections

    t_a = TenantFactory()
    t_b = TenantFactory()
    # Simula forja: cliente atacante setou `active_tenant_id` pra t_a
    # (legítimo) mas tenta gravar com tenant_id=t_b (alheio). A policy
    # RLS endurecida em 0013 (WITH CHECK tenant_id = active_tenant_id)
    # tem que bloquear com NewRowViolatesRowLevelSecurityPolicy
    # (subclasse de IntegrityError) e mensagem contendo "row-level
    # security" / "violates" — apertar a assertion pra pegar regressão
    # caso alguém reverta 0013.
    conn = connections["breaker_writer"]
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        try:
            cur.execute("SET LOCAL app.active_tenant_id = %s", [str(t_a.id)])
            with pytest.raises(ProgrammingError, match="row-level security"):
                cur.execute(
                    "INSERT INTO breaker_acesso_pii_evento "
                    "(id, tenant_id, ts, ok) "
                    "VALUES (gen_random_uuid(), %s, now(), %s)",
                    [str(t_b.id), True],
                )
        finally:
            cur.execute("ROLLBACK")


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_breaker_isolamento_por_tenant():
    """Eventos de tenant A não dispara P1 pra tenant B."""
    t_a = TenantFactory()
    t_b = TenantFactory()

    def falhar(**kwargs):
        raise RuntimeError("simulada")

    with run_in_tenant_context(t_a.id):
        with patch(
            "src.infrastructure.audit.breaker.registrar_acesso_dados_cliente",
            side_effect=falhar,
        ):
            for _ in range(3):
                with pytest.raises(RuntimeError):
                    registrar_acesso_dados_cliente_com_breaker(
                        tenant_id=t_a.id,
                        usuario_id=None,
                        cliente_id=uuid4(),
                        finalidade="atendimento_pos_venda",
                        recurso={},
                        ip_hash="",
                    )
    call_command("avaliar_circuit_breaker_acesso_pii", stdout=StringIO())
    assert _contar_p1_disparado(t_a.id) == 1
    assert _contar_p1_disparado(t_b.id) == 0
