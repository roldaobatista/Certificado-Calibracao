"""M8 Fatia 1b-numeração (T-CER-031/032/033) — número VISÍVEL sem buracos.

Puros: `proximo_sequencial` (densidade/reuso), `slug_certificado` (sanitização),
`montar_numero_certificado` (formato VO). PG-real: reserva→confirma→sem-buraco,
reserva→expira→reusa, confirmação one-shot, anti-reuso de número CONFIRMADO (trigger),
consecutividade no INSERT (trigger) e virada anual. GATE-CER-DRILL-LOCAL (concorrência
cronometrada real = T-CER-034 Wave A).
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.db import DatabaseError
from django.utils import timezone
from src.domain.metrologia.certificados.numeracao import (
    montar_numero_certificado,
    proximo_sequencial,
    slug_certificado,
)
from src.infrastructure.certificados.models import NumeroCertificadoReservado
from src.infrastructure.metrologia.certificados.repositories import (
    DjangoNumeracaoCertificadoRepository,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

ANO = 2026


# =============================================================
# Puros (sem Django)
# =============================================================
def test_proximo_sequencial_vazio_comeca_em_1():
    assert proximo_sequencial([]) == 1


def test_proximo_sequencial_denso_avanca():
    assert proximo_sequencial([1, 2, 3]) == 4


def test_proximo_sequencial_reusa_menor_buraco():
    # reserva expirada liberou o 2 → reusa o 2 (densidade NIT-DICLA-021).
    assert proximo_sequencial([1, 3]) == 2
    assert proximo_sequencial([2, 3]) == 1


def test_slug_certificado_sanitiza_hifen_e_caixa():
    assert slug_certificado("balancas-ab12ef") == "BALANCASAB12EF"
    assert slug_certificado("xy") == "XY"


def test_slug_certificado_fallback_curto():
    # < 2 chars vira slug determinístico válido (regex {2,16}).
    assert len(slug_certificado("a")) >= 2
    assert slug_certificado("a").isalnum()


def test_montar_numero_formato_visivel():
    num = montar_numero_certificado(tenant_slug="balancas", ano=2026, sequencial=42)
    assert num.value == "BALANCAS-2026-000042"
    assert num.sequencial == 42
    assert num.ano == 2026


# =============================================================
# PG-real — reserva → confirma → densidade
# =============================================================
def _tenant(prefix: str):
    return TenantFactory(slug=f"{prefix}{uuid4().hex[:6]}")


@pytest.mark.django_db(transaction=True)
def test_reserva_confirma_sequencia_sem_buraco():
    tenant = _tenant("numseq")
    repo = DjangoNumeracaoCertificadoRepository()
    with run_in_tenant_context(tenant.id):
        r1 = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=ANO, correlation_id=uuid4()
        )
        assert repo.confirmar_numero(reserva_id=r1.id, tenant_id=tenant.id)
        r2 = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=ANO, correlation_id=uuid4()
        )
        assert repo.confirmar_numero(reserva_id=r2.id, tenant_id=tenant.id)
    assert r1.sequencial == 1
    assert r2.sequencial == 2
    assert r1.numero_certificado.endswith("-2026-000001")
    assert r2.numero_certificado.endswith("-2026-000002")


@pytest.mark.django_db(transaction=True)
def test_reserva_expira_reusa_numero():
    tenant = _tenant("numreuse")
    repo = DjangoNumeracaoCertificadoRepository()
    with run_in_tenant_context(tenant.id):
        r1 = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=ANO, correlation_id=uuid4()
        )
        # força expiração da reserva 1 (não confirmada)
        NumeroCertificadoReservado.objects.filter(id=r1.id).update(
            ttl_expira_em=timezone.now() - timedelta(minutes=1)
        )
        liberados = repo.liberar_expirados(tenant_id=tenant.id, ano=ANO)
        assert liberados == 1
        r2 = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=ANO, correlation_id=uuid4()
        )
    assert r1.sequencial == 1
    assert r2.sequencial == 1  # reusa o número liberado — densidade


@pytest.mark.django_db(transaction=True)
def test_confirmar_numero_one_shot():
    tenant = _tenant("numone")
    repo = DjangoNumeracaoCertificadoRepository()
    with run_in_tenant_context(tenant.id):
        r = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=ANO, correlation_id=uuid4()
        )
        assert repo.confirmar_numero(reserva_id=r.id, tenant_id=tenant.id) is True
        # 2ª confirmação não passa (já confirmado).
        assert repo.confirmar_numero(reserva_id=r.id, tenant_id=tenant.id) is False


@pytest.mark.django_db(transaction=True)
def test_confirmar_reserva_expirada_falha():
    tenant = _tenant("numexp")
    repo = DjangoNumeracaoCertificadoRepository()
    with run_in_tenant_context(tenant.id):
        r = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=ANO, correlation_id=uuid4()
        )
        NumeroCertificadoReservado.objects.filter(id=r.id).update(
            ttl_expira_em=timezone.now() - timedelta(seconds=1)
        )
        assert repo.confirmar_numero(reserva_id=r.id, tenant_id=tenant.id) is False


@pytest.mark.django_db(transaction=True)
def test_numero_confirmado_nao_pode_ser_deletado():
    """Cancelamento PRESERVA o número (trigger block_delete_confirmado)."""
    tenant = _tenant("numdel")
    repo = DjangoNumeracaoCertificadoRepository()
    with run_in_tenant_context(tenant.id):
        r = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=ANO, correlation_id=uuid4()
        )
        repo.confirmar_numero(reserva_id=r.id, tenant_id=tenant.id)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        NumeroCertificadoReservado.objects.filter(id=r.id).delete()


@pytest.mark.django_db(transaction=True)
def test_insert_fora_de_sequencia_bloqueia():
    """Trigger de consecutividade: pular número (buraco) é proibido."""
    tenant = _tenant("numgap")
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        NumeroCertificadoReservado.objects.create(
            tenant=tenant, tipo="CERTIFICADO", ano=ANO, sequencial=5,
            ttl_expira_em=timezone.now() + timedelta(minutes=5),
        )


@pytest.mark.django_db(transaction=True)
def test_virada_anual_reinicia_sequencia():
    tenant = _tenant("numano")
    repo = DjangoNumeracaoCertificadoRepository()
    with run_in_tenant_context(tenant.id):
        r2026 = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=2026, correlation_id=uuid4()
        )
        repo.confirmar_numero(reserva_id=r2026.id, tenant_id=tenant.id)
        r2027 = repo.reservar_numero(
            tenant_id=tenant.id, tenant_slug=tenant.slug, ano=2027, correlation_id=uuid4()
        )
    assert r2026.sequencial == 1
    assert r2027.sequencial == 1  # novo ano reinicia
    assert r2026.numero_certificado.endswith("-2026-000001")
    assert r2027.numero_certificado.endswith("-2027-000001")
