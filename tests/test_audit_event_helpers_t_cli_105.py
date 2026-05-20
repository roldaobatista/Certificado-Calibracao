"""T-CLI-105 / SANEA-08 — testes do helper único `publicar_evento`.

Cobertura:

1. test_publicar_evento_grava_na_cadeia_e_sanitiza — happy path:
   payload contém UUID e regex de CPF; sanitizado em ESCRITA antes de gravar.
2. test_publicar_evento_tenant_mismatch — tenant_id diverge do contexto
   ativo → TenantMismatch.
3. test_publicar_evento_sem_contexto_tenant — sem app.active_tenant_id e
   sem modo_sistema → TenantMismatch.
4. test_publicar_evento_modo_sistema — tenant_id=None + run_as_system → ok.
5. test_publicar_evento_outbox_true_ainda_nao_implementado — OutboxNaoImplementado.
6. test_publicar_evento_escopo_authz_nao_implementado.
7. test_publicar_evento_cadeia_false_outbox_false_invalido — ValueError.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.infrastructure.audit.event_helpers import (
    OutboxNaoImplementado,
    TenantMismatch,
    publicar_evento,
)
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.multitenant.connection import run_as_system, run_in_tenant_context

from tests.factories import TenantFactory


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_grava_na_cadeia_e_sanitiza():
    tenant = TenantFactory()
    cliente_uuid = uuid4()
    payload = {
        "cliente_id": str(cliente_uuid),
        "cpf_falso": "12345678901",  # regex PII detecta
        "nota": "ok",
    }
    with run_in_tenant_context(tenant.id):
        ev = publicar_evento(
            acao="cliente.criado",
            payload=payload,
            causation_id=uuid4(),
            tenant_id=tenant.id,
            outbox=False,
        )
    assert ev.cadeia_linha_id is not None
    assert ev.outbox_enfileirado is False

    # Linha foi gravada com payload sanitizado
    with run_in_tenant_context(tenant.id):
        linha = Auditoria.objects.get(id=ev.cadeia_linha_id)
    # UUID preservado (T-CLI-105 garantia 1 — sanitizar_payload_audit isenta UUID)
    assert linha.payload_jsonb["cliente_id"] == str(cliente_uuid)
    # CPF (regex PII) redatado
    assert linha.payload_jsonb["cpf_falso"] == "[REDACTED]"


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_tenant_mismatch():
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    with run_in_tenant_context(tenant_a.id):
        with pytest.raises(TenantMismatch, match="diverge do contexto"):
            publicar_evento(
                acao="cliente.criado",
                payload={"x": 1},
                causation_id=uuid4(),
                tenant_id=tenant_b.id,
                outbox=False,
            )


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_sem_contexto_tenant():
    tenant = TenantFactory()
    # Sem run_in_tenant_context — contexto vazio
    with pytest.raises(TenantMismatch, match="sem app.active_tenant_id"):
        publicar_evento(
            acao="x",
            payload={},
            causation_id=uuid4(),
            tenant_id=tenant.id,
            outbox=False,
        )


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_modo_sistema():
    with run_as_system():
        ev = publicar_evento(
            acao="job.contagem",
            payload={"qtd": 0},
            causation_id=uuid4(),
            tenant_id=None,
            outbox=False,
        )
    assert ev.cadeia_linha_id is not None


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_outbox_true_ainda_nao_implementado():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        with pytest.raises(OutboxNaoImplementado):
            publicar_evento(
                acao="cliente.criado",
                payload={},
                causation_id=uuid4(),
                tenant_id=tenant.id,
                outbox=True,
            )


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_escopo_authz_nao_implementado():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        with pytest.raises(NotImplementedError, match="authz"):
            publicar_evento(
                acao="authz.denied",
                payload={},
                causation_id=uuid4(),
                tenant_id=tenant.id,
                escopo="authz",
                outbox=False,
            )


@pytest.mark.django_db(transaction=True)
def test_publicar_evento_cadeia_false_outbox_false_invalido():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        with pytest.raises(ValueError, match="não faz sentido"):
            publicar_evento(
                acao="x",
                payload={},
                causation_id=uuid4(),
                tenant_id=tenant.id,
                cadeia=False,
                outbox=False,
            )
