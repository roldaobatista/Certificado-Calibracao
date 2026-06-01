"""M9 Fatia 1b (T-LIC-020) — drill PG-real de schema + RLS + WORM.

Cobre o COMPORTAMENTO em PG real (o que o hook estático não garante):
- INV-TENANT-001/002/003: RLS isola documentos entre tenants (UNHAPPY cross-tenant).
- INV-LIC-WORM-001: revisao_documento + evento_emergencial_licenca append-only
  (UPDATE/DELETE RAISE); documento_regulatorio identidade imutável + block DELETE
  (Padrão B); campo mutável (observacao) muta OK; revogação one-shot.
GATE-LIC-DRILL-LOCAL. Padrão TST-004 (happy + unhappy). Cada RAISE aborta a
transação PG → cada `raises` isolado na própria transação (run_in_tenant_context).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from django.db import DatabaseError, connection
from django.utils import timezone
from src.infrastructure.metrologia.licencas_acreditacoes.models import (
    AlertaVencimento,
    BloqueioOperacional,
    DocumentoRegulatorio,
    EventoEmergencialLicenca,
    RevisaoDocumento,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

TABELAS_M9 = [
    "documento_regulatorio",
    "revisao_documento",
    "alerta_vencimento",
    "bloqueio_operacional",
    "evento_emergencial_licenca",
]


def _cria_documento(tenant, *, tipo: str = "ALVARA", numero: str = "123") -> DocumentoRegulatorio:
    with run_in_tenant_context(tenant.id):
        return DocumentoRegulatorio.objects.create(
            tenant=tenant, tipo=tipo, numero=numero, orgao_emissor="Prefeitura",
            vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2027, 1, 1),
            bloqueante=False, criado_por=uuid4(),
        )


def _cria_revisao(tenant, doc, *, n: int = 1) -> RevisaoDocumento:
    with run_in_tenant_context(tenant.id):
        return RevisaoDocumento.objects.create(
            tenant=tenant, documento=doc, numero_revisao=n,
            data_emissao=date(2026, 1, 1), data_validade=date(2027, 1, 1),
            anexo_id=uuid4(), anexo_sha256="a" * 64, motivo="CADASTRO_INICIAL",
            criado_por=uuid4(),
        )


def _cria_evento_emergencial(tenant, doc) -> EventoEmergencialLicenca:
    with run_in_tenant_context(tenant.id):
        bloq = BloqueioOperacional.objects.create(
            tenant=tenant, documento=doc, tipo_documento=doc.tipo,
            operacao_bloqueada="assinatura_certificado",
            data_inicio_bloqueio=datetime(2026, 6, 1, tzinfo=UTC),
        )
        return EventoEmergencialLicenca.objects.create(
            tenant=tenant, bloqueio=bloq, operacao_executada="assinatura_certificado",
            justificativa="j" * 100, justificativa_hash="b" * 64, admin_id=uuid4(),
            assinatura_a3_id=uuid4(), expira_em=datetime(2026, 6, 7, tzinfo=UTC),
        )


# =============================================================
# Estrutura — RLS FORCE + 4 policies por tabela
# =============================================================
@pytest.mark.django_db
def test_cinco_tabelas_m9_tem_rls_force_e_4_policies() -> None:
    with connection.cursor() as cur:
        for tabela in TABELAS_M9:
            cur.execute("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = %s;", [tabela])
            row = cur.fetchone()
            assert row == (True, True), f"{tabela} sem RLS FORCE"
            cur.execute("SELECT count(*) FROM pg_policies WHERE tablename = %s;", [tabela])
            assert cur.fetchone()[0] == 4, f"{tabela} não tem 4 policies"


# =============================================================
# RLS — isolamento cross-tenant (UNHAPPY)
# =============================================================
@pytest.mark.django_db
def test_rls_documento_nao_vaza_entre_tenants() -> None:
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    doc_a = _cria_documento(tenant_a, numero="AAA")

    # tenant B NÃO enxerga documento do tenant A.
    with run_in_tenant_context(tenant_b.id):
        assert not DocumentoRegulatorio.objects.filter(id=doc_a.id).exists()
        assert DocumentoRegulatorio.objects.count() == 0

    # tenant A enxerga o próprio.
    with run_in_tenant_context(tenant_a.id):
        assert DocumentoRegulatorio.objects.filter(id=doc_a.id).exists()


# =============================================================
# WORM — revisao_documento append-only (INV-LIC-WORM-001)
# =============================================================
@pytest.mark.django_db
def test_revisao_documento_update_bloqueado() -> None:
    tenant = TenantFactory()
    doc = _cria_documento(tenant)
    rev = _cria_revisao(tenant, doc)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError, match="append-only"):
        RevisaoDocumento.objects.filter(id=rev.id).update(data_validade=date(2028, 1, 1))


@pytest.mark.django_db
def test_revisao_documento_delete_bloqueado() -> None:
    tenant = TenantFactory()
    doc = _cria_documento(tenant)
    rev = _cria_revisao(tenant, doc)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError, match="append-only"):
        RevisaoDocumento.objects.filter(id=rev.id).delete()


# =============================================================
# WORM — evento_emergencial_licenca append-only (INV-033)
# =============================================================
@pytest.mark.django_db
def test_evento_emergencial_update_bloqueado() -> None:
    tenant = TenantFactory()
    doc = _cria_documento(tenant)
    ev = _cria_evento_emergencial(tenant, doc)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError, match="append-only"):
        EventoEmergencialLicenca.objects.filter(id=ev.id).update(justificativa="z" * 100)


@pytest.mark.django_db
def test_evento_emergencial_delete_bloqueado() -> None:
    tenant = TenantFactory()
    doc = _cria_documento(tenant)
    ev = _cria_evento_emergencial(tenant, doc)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError, match="append-only"):
        EventoEmergencialLicenca.objects.filter(id=ev.id).delete()


# =============================================================
# WORM — documento_regulatorio Padrão B (identidade imutável + block delete)
# =============================================================
@pytest.mark.django_db
def test_documento_delete_fisico_bloqueado() -> None:
    tenant = TenantFactory()
    doc = _cria_documento(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError, match="nao pode ser deletado"):
        DocumentoRegulatorio.objects.filter(id=doc.id).delete()


@pytest.mark.django_db
def test_documento_identidade_imutavel() -> None:
    tenant = TenantFactory()
    doc = _cria_documento(tenant, tipo="ALVARA", numero="123")
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError, match="identidade imutavel"):
        DocumentoRegulatorio.objects.filter(id=doc.id).update(numero="999")


@pytest.mark.django_db
def test_documento_campo_mutavel_ok() -> None:
    tenant = TenantFactory()
    doc = _cria_documento(tenant)
    with run_in_tenant_context(tenant.id):
        DocumentoRegulatorio.objects.filter(id=doc.id).update(
            observacao="renovação em curso", bloqueante=True
        )
        doc.refresh_from_db()
    assert doc.bloqueante is True
    assert doc.observacao == "renovação em curso"


@pytest.mark.django_db
def test_documento_revogacao_one_shot() -> None:
    tenant = TenantFactory()
    doc = _cria_documento(tenant)
    agora = timezone.now()
    with run_in_tenant_context(tenant.id):
        # 1ª revogação OK.
        DocumentoRegulatorio.objects.filter(id=doc.id).update(
            revogado_em=agora, motivo_revogacao="documento substituído por nova licença"
        )
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError, match="one-shot"):
        DocumentoRegulatorio.objects.filter(id=doc.id).update(
            revogado_em=agora + timedelta(days=1)
        )


# =============================================================
# UNIQUE idempotência de alertas (tenant, documento, janela_dias)
# =============================================================
@pytest.mark.django_db
def test_alerta_idempotente_por_janela() -> None:
    from django.db import IntegrityError

    tenant = TenantFactory()
    doc = _cria_documento(tenant)
    with run_in_tenant_context(tenant.id):
        AlertaVencimento.objects.create(
            tenant=tenant, documento=doc, data_disparo=date(2026, 9, 1),
            janela_dias=30, canal="DASHBOARD", destinatario_id=uuid4(),
        )
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        AlertaVencimento.objects.create(
            tenant=tenant, documento=doc, data_disparo=date(2026, 9, 1),
            janela_dias=30, canal="EMAIL", destinatario_id=uuid4(),
        )
