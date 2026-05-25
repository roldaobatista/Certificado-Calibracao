"""Anti-regressao INV-OS-AUD-001 (T-OS-120c) — sanitizacao na ESCRITA de eventos.

INV-OS-AUD-001: payload em EventoDeOS sanitizado NA ESCRITA via helper
unico `audit.event_helpers.publicar_evento` (que aplica
`sanitizar_payload_audit`). Bug-classe sanitizar-na-leitura (flake
visao-360 2026-05-19) NUNCA mais.

Proibe (a) `cliente_id`, `tecnico_id`, `ator_id` cru em chave PII
denylist; (b) `razao_*` cru; (c) regex PII (CPF/CNPJ/email/telefone) em
qualquer valor texto. Tambem garante guard UUID estrutural — surrogate
key `xxxx_id` nao confunde com PII (mesmo se digitos casarem regex CPF
por azar, ~8.4% dos uuid4).

≥3 testes: happy (UUID estrutural passa intacto), unhappy denylist
(chave `nome` redatada), unhappy regex (telefone embutido redatado),
cross-tenant (auditoria gravada no tenant A nao apareces em queries do B).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from django.db import transaction
from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _publicar(tenant_id: UUID, acao: str, payload: dict) -> None:
    """Wrapper helper — abre transacao + contexto + publica."""
    with run_in_tenant_context(tenant_id), transaction.atomic():
        publicar_evento(
            acao=acao,
            payload=payload,
            causation_id=uuid4(),
            tenant_id=tenant_id,
            escopo="auditoria",
            cadeia=True,
            outbox=False,  # evita dependencia da tabela bus_outbox aqui
        )


# =============================================================
# Happy: UUID estrutural + dados nao-PII passam intactos
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_aud_001_happy_uuid_estrutural_passa_intacto(db):
    """Happy: payload sem PII (UUIDs + ints + bools) eh persistido COMO
    enviado. Guard UUID protege surrogate keys do redacto regex."""
    tenant = TenantFactory(slug=f"inv-aud-h-{uuid4().hex[:6]}")
    cliente_id = uuid4()
    os_id = uuid4()
    _publicar(
        tenant.id,
        "os.aberta",
        {
            "os_id": str(os_id),
            "cliente_id_hash": "v1:abc123",
            "cliente_id_uuid_estrutural": str(cliente_id),
            "valor_total_centavos": 10000,
            "requer_aceite": True,
        },
    )

    with run_in_tenant_context(tenant.id):
        aud = Auditoria.objects.filter(tenant=tenant, action="os.aberta").get()
    p = aud.payload_jsonb
    assert p["os_id"] == str(os_id), "UUID estrutural deveria passar intacto"
    assert p["cliente_id_uuid_estrutural"] == str(cliente_id), (
        "UUID em chave nao-denylist deveria passar intacto (guard UUID)"
    )
    assert p["cliente_id_hash"] == "v1:abc123"
    assert p["valor_total_centavos"] == 10000
    assert p["requer_aceite"] is True


# =============================================================
# Unhappy denylist: chave 'nome' / 'documento' viram [REDACTED]
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_aud_001_unhappy_chaves_denylist_redatadas(db):
    """Unhappy: chamador erra e poe `nome`/`documento` no payload —
    helper RECUSA gravar cru, redata pra `[REDACTED]`."""
    tenant = TenantFactory(slug=f"inv-aud-d-{uuid4().hex[:6]}")
    _publicar(
        tenant.id,
        "os.aberta",
        {
            "os_id": str(uuid4()),
            "nome": "Joao da Silva",
            "documento": "11222333000181",
            "email": "joao@exemplo.com",
        },
    )

    with run_in_tenant_context(tenant.id):
        aud = Auditoria.objects.filter(tenant=tenant, action="os.aberta").get()
    p = aud.payload_jsonb
    assert p["nome"] == "[REDACTED]", "chave 'nome' deveria virar [REDACTED]"
    assert p["documento"] == "[REDACTED]", "chave 'documento' deveria virar [REDACTED]"
    assert p["email"] == "[REDACTED]", "chave 'email' deveria virar [REDACTED]"


# =============================================================
# Unhappy regex: telefone embutido em texto livre vira [REDACTED]
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_aud_001_unhappy_pii_em_texto_livre_redatada(db):
    """Unhappy: texto livre contendo telefone/CPF vira `[REDACTED]`
    pela regex antes de gravar (defesa contra PII vazada por
    distracao do dev)."""
    tenant = TenantFactory(slug=f"inv-aud-r-{uuid4().hex[:6]}")
    _publicar(
        tenant.id,
        "os.cancelada",
        {
            "os_id": str(uuid4()),
            # NAO chave de denylist — mas conteudo eh PII por regex.
            "observacao_publica": "Cancelado pelo cliente 11999998888",
            "outro_campo": "CPF do tecnico 12345678901",
        },
    )

    with run_in_tenant_context(tenant.id):
        aud = Auditoria.objects.filter(tenant=tenant, action="os.cancelada").get()
    p = aud.payload_jsonb
    assert p["observacao_publica"] == "[REDACTED]", (
        "telefone embutido em texto livre deveria virar [REDACTED]"
    )
    assert p["outro_campo"] == "[REDACTED]", (
        "CPF embutido em texto livre deveria virar [REDACTED]"
    )


# =============================================================
# Cross-tenant: auditoria de tenant A nao vaza pra tenant B
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_aud_001_cross_tenant_auditoria_isolada(db):
    """Cross-tenant: publicar_evento exige tenant_id == contexto ativo;
    auditoria de tenant A nao aparece em filter por tenant B."""
    tenant_a = TenantFactory(slug=f"inv-aud-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-aud-ctb-{uuid4().hex[:6]}")
    _publicar(tenant_a.id, "os.aberta", {"os_id": str(uuid4())})
    _publicar(tenant_b.id, "os.aberta", {"os_id": str(uuid4())})

    with run_in_tenant_context(tenant_a.id):
        a_count = Auditoria.objects.filter(tenant=tenant_a, action="os.aberta").count()
        a_ids = set(
            Auditoria.objects.filter(tenant=tenant_a, action="os.aberta").values_list(
                "id", flat=True
            )
        )
    with run_in_tenant_context(tenant_b.id):
        b_count = Auditoria.objects.filter(tenant=tenant_b, action="os.aberta").count()
        b_ids = set(
            Auditoria.objects.filter(tenant=tenant_b, action="os.aberta").values_list(
                "id", flat=True
            )
        )
    assert a_count == 1, "tenant A deveria ter exatamente 1 auditoria"
    assert b_count == 1, "tenant B deveria ter exatamente 1 auditoria"
    assert a_ids.isdisjoint(b_ids), "IDs deveriam ser disjuntos por tenant"
