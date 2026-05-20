"""T-CLI-107 — testes da tabela `bus_outbox` + `publicar_evento(outbox=True)`.

Cobertura:

1. test_publicar_evento_outbox_true_grava_linha — happy path: INSERT
   no `bus_outbox` quando outbox=True; envelope contém payload sanitizado.
2. test_publicar_evento_outbox_idempotente_em_causation_acao — repetir
   chamada com mesmo (causation_id, acao) NÃO duplica (ON CONFLICT
   DO NOTHING). 2ª chamada retorna outbox_enfileirado=False.
3. test_publicar_evento_outbox_sob_rls_tenant_a_nao_ve_b — RLS isola
   linhas por tenant (SELECT em contexto B não enxerga linhas de A).
4. test_publicar_evento_outbox_payload_ja_sanitizado — CPF redatado
   também dentro do envelope_jsonb (sanitize em ESCRITA — SEC-SANITIZE-001).
5. test_publicar_evento_outbox_no_mesmo_atomic_do_caller — cadeia +
   outbox commitam JUNTOS ou rolam JUNTOS (contrato 1 P2).
6. test_acao_check_constraint_rejeita_string_com_cpf — BLOQ-A1: CHECK
   constraint anti-PII na coluna `acao`.
7. test_envelope_check_constraint_rejeita_64kb_plus — MED-2: limite
   tamanho do envelope.
8. test_predicado_rls_bus_outbox_byte_a_byte_igual_ao_de_auditoria —
   BLOQ-A: garante que a policy SELECT do bus_outbox usa o MESMO
   predicate da `auditoria` (CASE modo_sistema/require_tenant_ctx).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import IntegrityError, connection, transaction
from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _contar_linhas_outbox_total() -> int:
    """Conta linhas no outbox via system mode (bypass RLS pra ver tudo)."""
    from src.infrastructure.multitenant.connection import run_as_system

    with run_as_system():
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM bus_outbox")
            return cur.fetchone()[0]


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_outbox_true_grava_linha():
    tenant = TenantFactory()
    cid = uuid4()
    with run_in_tenant_context(tenant.id):
        ev = publicar_evento(
            acao="cliente.criado",
            payload={"nome": "Foo Bar"},
            causation_id=cid,
            tenant_id=tenant.id,
            outbox=True,
        )
    assert ev.outbox_enfileirado is True
    # Linha gravada
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT causation_id, acao, tenant_id FROM bus_outbox " "WHERE causation_id = %s",
                [str(cid)],
            )
            row = cur.fetchone()
    assert row is not None
    assert str(row[0]) == str(cid)
    assert row[1] == "cliente.criado"
    assert str(row[2]) == str(tenant.id)


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_outbox_idempotente_em_causation_acao():
    tenant = TenantFactory()
    cid = uuid4()
    with run_in_tenant_context(tenant.id):
        ev1 = publicar_evento(
            acao="cliente.criado",
            payload={"v": 1},
            causation_id=cid,
            tenant_id=tenant.id,
            outbox=True,
        )
    with run_in_tenant_context(tenant.id):
        ev2 = publicar_evento(
            acao="cliente.criado",
            payload={"v": 2},  # payload diferente, mas (causation_id, acao) igual
            causation_id=cid,
            tenant_id=tenant.id,
            outbox=True,
        )
    assert ev1.outbox_enfileirado is True
    assert ev2.outbox_enfileirado is False  # ON CONFLICT DO NOTHING
    # Apenas UMA linha existe no outbox
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM bus_outbox WHERE causation_id = %s",
                [str(cid)],
            )
            assert cur.fetchone()[0] == 1


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_outbox_sob_rls_tenant_a_nao_ve_b():
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    cid_a = uuid4()
    cid_b = uuid4()
    with run_in_tenant_context(tenant_a.id):
        publicar_evento(
            acao="cliente.criado",
            payload={"a": True},
            causation_id=cid_a,
            tenant_id=tenant_a.id,
            outbox=True,
        )
    with run_in_tenant_context(tenant_b.id):
        publicar_evento(
            acao="cliente.criado",
            payload={"b": True},
            causation_id=cid_b,
            tenant_id=tenant_b.id,
            outbox=True,
        )
    # Em contexto de B: SELECT NÃO vê linha de A
    with run_in_tenant_context(tenant_b.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT causation_id FROM bus_outbox WHERE causation_id = %s",
                [str(cid_a)],
            )
            assert cur.fetchone() is None
            cur.execute(
                "SELECT causation_id FROM bus_outbox WHERE causation_id = %s",
                [str(cid_b)],
            )
            assert cur.fetchone() is not None


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_outbox_payload_ja_sanitizado():
    tenant = TenantFactory()
    cid = uuid4()
    with run_in_tenant_context(tenant.id):
        publicar_evento(
            acao="cliente.criado",
            payload={"cpf_falso": "12345678901", "nota": "ok"},
            causation_id=cid,
            tenant_id=tenant.id,
            outbox=True,
        )
    import json as _json

    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb FROM bus_outbox WHERE causation_id = %s",
                [str(cid)],
            )
            envelope_raw = cur.fetchone()[0]
    # Cursor cru retorna jsonb como str (sem adapter do ORM)
    envelope = envelope_raw if isinstance(envelope_raw, dict) else _json.loads(envelope_raw)
    # Payload dentro do envelope foi sanitizado (CPF redatado)
    assert envelope["payload"]["cpf_falso"] == "[REDACTED]"
    assert envelope["payload"]["nota"] == "ok"


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_outbox_no_mesmo_atomic_do_caller():
    """Cadeia + outbox commitam JUNTOS ou rolam JUNTOS — contrato 1 P2."""
    tenant = TenantFactory()
    cid = uuid4()
    n_antes_audit = _contar_linhas_outbox_total()
    # Caller abre atomic, faz publicar_evento, depois LEVANTA — rollback
    with pytest.raises(RuntimeError, match="rollback intencional"):
        with run_in_tenant_context(tenant.id):
            with transaction.atomic():
                publicar_evento(
                    acao="cliente.criado",
                    payload={"v": 1},
                    causation_id=cid,
                    tenant_id=tenant.id,
                    outbox=True,
                )
                raise RuntimeError("rollback intencional")
    # Outbox NÃO ganhou linha — atomicidade do caller respeitada.
    n_depois = _contar_linhas_outbox_total()
    assert n_depois == n_antes_audit


@pytest.mark.django_db(transaction=True)
def test_acao_check_constraint_rejeita_string_com_cpf():
    """BLOQ-A1: CHECK constraint anti-PII rejeita slug com dígitos longos."""
    tenant = TenantFactory()
    # `assert_acao_canonica` em Python já rejeita antes do banco; pra exercitar
    # o CHECK constraint vamos fazer INSERT cru sob run_as_system.
    from src.infrastructure.multitenant.connection import run_as_system

    with run_as_system():
        with pytest.raises(IntegrityError, match="bus_outbox_acao_enum_semantico"):
            with connection.cursor() as cur:
                cur.execute(
                    "INSERT INTO bus_outbox (id, causation_id, acao, envelope_jsonb, "
                    "tenant_id, criado_em, tentativas) "
                    "VALUES (gen_random_uuid(), %s, %s, '{}'::jsonb, NULL, now(), 0)",
                    [str(uuid4()), "cliente.cpf.12345678900"],
                )
    # Pra evitar tenant órfão
    _ = tenant


@pytest.mark.django_db(transaction=True)
def test_envelope_check_constraint_rejeita_64kb_plus():
    """MED-2: limite de tamanho do envelope_jsonb < 64 KiB."""
    from src.infrastructure.multitenant.connection import run_as_system

    envelope_grande = {"x": "a" * 70000}  # > 64 KiB já com overhead JSONB
    import json as _json

    with run_as_system():
        with pytest.raises(IntegrityError, match="bus_outbox_envelope_limite_64kb"):
            with connection.cursor() as cur:
                cur.execute(
                    "INSERT INTO bus_outbox (id, causation_id, acao, envelope_jsonb, "
                    "tenant_id, criado_em, tentativas) "
                    "VALUES (gen_random_uuid(), %s, %s, %s::jsonb, NULL, now(), 0)",
                    [str(uuid4()), "sistema.tenant_provisionado", _json.dumps(envelope_grande)],
                )


@pytest.mark.django_db(transaction=True)
def test_predicado_rls_bus_outbox_divergencia_justificada_de_auditoria():
    """BLOQ-A tech-lead REAVALIADO: outbox precisa cross-tenant em modo_sistema
    (worker drena pendências de TODOS os tenants). Divergência justificada:
    em modo_sistema, `bus_outbox` vê TUDO; `auditoria` só vê tenant_id IS NULL.

    Este teste cobre a INTENÇÃO da divergência (modo_sistema TRUE no bus_outbox)
    + a parte que segue idêntica (modo tenant: require_tenant_ctx).
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT pg_get_expr(polqual, polrelid) "
            "FROM pg_policy WHERE polname = 'bus_outbox_tenant_isolation_select'"
        )
        bus_pred = cur.fetchone()[0]
        cur.execute(
            "SELECT pg_get_expr(polqual, polrelid) "
            "FROM pg_policy WHERE polname = 'auditoria_chain_select'"
        )
        audit_pred = cur.fetchone()[0]
    # bus_outbox: modo_sistema vê TUDO; senão filtra por tenant_ids do contexto.
    assert "modo_sistema" in bus_pred
    assert "require_tenant_ctx" in bus_pred
    # Divergência: bus_outbox NÃO tem "tenant_id IS NULL" no ramo modo_sistema
    # (vê TUDO). auditoria TEM "tenant_id IS NULL" no ramo modo_sistema.
    audit_modo_sistema_clause = audit_pred.split("ELSE")[0]
    bus_modo_sistema_clause = bus_pred.split("ELSE")[0]
    assert "tenant_id IS NULL" in audit_modo_sistema_clause
    assert "tenant_id IS NULL" not in bus_modo_sistema_clause
