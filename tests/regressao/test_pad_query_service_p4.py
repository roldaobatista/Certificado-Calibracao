"""M5 P4 (T-PAD-030/032) — porta `padrao_bloqueado_para_uso` fail-CLOSED.

GATE-PAD-PORTA-M4: prova que a porta rejeita TODOS os vetores de sinistro E&O
(padrao vencido / VI reprovada / PT rejeitada / carta violada / recal pendente /
origem revogada / estado != EM_USO / cross-tenant) e libera so o padrao saudavel.
Tambem cobre snapshot_para_uso e buscar_disponivel_para_calibracao. PG-real.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone
from src.domain.metrologia.padroes.enums import (
    DecisaoRTCarta,
    EstadoPadrao,
    RegraWesternElectric,
    ResultadoPT,
    ResultadoVI,
)
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)
from src.infrastructure.metrologia.padroes import mappers, query_service
from src.infrastructure.metrologia.padroes.models import (
    AnaliseCartaControle,
    IntercomparacaoPT,
    PadraoMetrologico,
    VerificacaoIntermediaria,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

HOJE = date(2026, 6, 1)


def _cria_padrao(tenant, **kw):
    defaults = {
        "tenant": tenant,
        "numero_serie": f"PAD-{uuid4().hex[:8]}",
        "fabricante": "Mettler",
        "modelo": "XPR",
        "subtipo": "PRINCIPAL",
        "grandezas": mappers.grandezas_para_json((Grandeza.MASSA,)),
        "faixas": mappers.faixas_para_json(
            (FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),)
        ),
        "incertezas_certificado": mappers.incertezas_para_json(
            (IncertezaExpandida(Decimal("0.001"), Decimal("2"), Decimal("0.9545"), "g"),)
        ),
        "vinculacao": "INMETRO",
        "classe": "E2",
        "validade_certificado_rastreabilidade": date(2027, 1, 1),
        "proximo_recal": date(2027, 1, 1),
        "intervalo_recal_meses": 12,
        "intervalo_vi_meses": 3,
        "criterio_intervalo": "cl. 6.4.7 historico de estabilidade",
        "estado": "EM_USO",
        "vigencia_inicio": timezone.now(),
    }
    defaults.update(kw)
    with run_in_tenant_context(tenant.id):
        return PadraoMetrologico.objects.create(**defaults)


# --------------------------------------------------------------------------
# padrao_bloqueado_para_uso — happy
# --------------------------------------------------------------------------
@pytest.mark.django_db(transaction=True)
def test_padrao_saudavel_nao_bloqueia():
    tenant = TenantFactory(slug=f"pq-ok-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
    assert bloqueado is False, motivo
    assert motivo == ""


# --------------------------------------------------------------------------
# Bloqueios diretos (campos do padrao)
# --------------------------------------------------------------------------
@pytest.mark.django_db(transaction=True)
def test_padrao_inexistente_bloqueia_fail_closed():
    tenant = TenantFactory(slug=f"pq-inx-{uuid4().hex[:6]}")
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(uuid4(), hoje=HOJE)
    assert bloqueado is True
    assert "inexistente" in motivo


@pytest.mark.django_db(transaction=True)
def test_recal_vencido_bloqueia():
    tenant = TenantFactory(slug=f"pq-venc-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant, proximo_recal=date(2026, 1, 1))  # antes de HOJE
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
    assert bloqueado is True
    assert "recal vencido" in motivo


@pytest.mark.django_db(transaction=True)
def test_cert_rastreabilidade_vencido_bloqueia():
    tenant = TenantFactory(slug=f"pq-cert-{uuid4().hex[:6]}")
    padrao = _cria_padrao(
        tenant, validade_certificado_rastreabilidade=date(2026, 1, 1)
    )
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
    assert bloqueado is True
    assert "rastreabilidade vencido" in motivo


@pytest.mark.django_db(transaction=True)
def test_estado_nao_em_uso_bloqueia():
    tenant = TenantFactory(slug=f"pq-est-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant, estado=EstadoPadrao.EM_RECAL_EXTERNO.value)
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
    assert bloqueado is True
    assert "EM_USO" in motivo


@pytest.mark.django_db(transaction=True)
def test_rastreabilidade_revogada_bloqueia():
    tenant = TenantFactory(slug=f"pq-rev-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant, rastreabilidade_origem_revogada=True)
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
    assert bloqueado is True
    assert "rastreabilidade da origem revogada" in motivo


@pytest.mark.django_db(transaction=True)
def test_soft_deletado_bloqueia():
    tenant = TenantFactory(slug=f"pq-soft-{uuid4().hex[:6]}")
    padrao = _cria_padrao(
        tenant,
        estado=EstadoPadrao.BAIXADO.value,
        revogado_em=timezone.now(),
        motivo_revogacao="fora de uso por decisao tecnica",
    )
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
    assert bloqueado is True
    assert "revogado" in motivo


# --------------------------------------------------------------------------
# Bloqueios por entidades filhas
# --------------------------------------------------------------------------
@pytest.mark.django_db(transaction=True)
def test_ultima_vi_reprovada_bloqueia():
    tenant = TenantFactory(slug=f"pq-vi-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        VerificacaoIntermediaria.objects.create(
            tenant=tenant,
            padrao=padrao,
            data_vi=datetime(2026, 5, 1, tzinfo=UTC),
            executor_id_hash="v1$e",
            metodo_canonicalizado="m",
            metodo_hash="v1$h",
            resultado=ResultadoVI.REPROVADO.value,
            acao_corretiva_canonicalizada="acao corretiva aplicada conforme cl 7.10",
            acao_corretiva_hash="v1$a",
        )
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
    assert bloqueado is True
    assert "REPROVADA" in motivo


@pytest.mark.django_db(transaction=True)
def test_pt_rejeitada_sem_nc_bloqueia():
    tenant = TenantFactory(slug=f"pq-pt-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        IntercomparacaoPT.objects.create(
            tenant=tenant,
            padrao=padrao,
            lab_organizador="INMETRO",
            protocolo="PT-1",
            data_inicio=datetime(2026, 4, 1, tzinfo=UTC),
            resultado=ResultadoPT.REJEITADO.value,
            data_resultado=datetime(2026, 5, 1, tzinfo=UTC),
        )
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
    assert bloqueado is True
    assert "REJEITADA" in motivo


# --------------------------------------------------------------------------
# Carta Shewhart — perfil A bloqueia; perfil nao-A nao (INV-PAD-008)
# --------------------------------------------------------------------------
def _insere_serie_tendencia(tenant, padrao):
    with run_in_tenant_context(tenant.id):
        for i in range(1, 8):  # 7 desvios crescentes -> tendencia (R5)
            VerificacaoIntermediaria.objects.create(
                tenant=tenant,
                padrao=padrao,
                data_vi=datetime(2026, 1, i, tzinfo=UTC),
                executor_id_hash="v1$e",
                metodo_canonicalizado="m",
                metodo_hash="v1$h",
                resultado=ResultadoVI.APROVADO.value,
                desvio_observado=Decimal(i),
            )


@pytest.mark.django_db(transaction=True)
def test_carta_violada_perfil_a_sem_analise_bloqueia():
    tenant = TenantFactory(slug=f"pq-cartaA-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    _insere_serie_tendencia(tenant, padrao)
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
            padrao.id, tenant_e_perfil_a=True, hoje=HOJE
        )
    assert bloqueado is True
    assert "Shewhart" in motivo


@pytest.mark.django_db(transaction=True)
def test_carta_violada_perfil_nao_a_nao_bloqueia():
    tenant = TenantFactory(slug=f"pq-cartaN-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    _insere_serie_tendencia(tenant, padrao)
    with run_in_tenant_context(tenant.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
            padrao.id, tenant_e_perfil_a=False, hoje=HOJE
        )
    assert bloqueado is False, motivo


@pytest.mark.django_db(transaction=True)
def test_carta_violada_com_analise_liberadora_nao_bloqueia():
    tenant = TenantFactory(slug=f"pq-cartaL-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    _insere_serie_tendencia(tenant, padrao)
    with run_in_tenant_context(tenant.id):
        AnaliseCartaControle.objects.create(
            tenant=tenant,
            padrao=padrao,
            regra_violada=RegraWesternElectric.REGRA_5_TENDENCIA_7.value,
            pontos_referenciados_ids=[str(uuid4())],
            linha_central="4",
            ucl="10",
            lcl="-2",
            sigma="2",
            n_pontos=7,
            janela_meses=24,
            versao_motor_shewhart="shewhart-1.0.0",
            decisao_rt=DecisaoRTCarta.ACEITO_COM_JUSTIFICATIVA.value,
            justificativa_canonicalizada="tendencia aceita — dentro da tolerancia tecnica",
            justificativa_hash="v1$j",
        )
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
            padrao.id, tenant_e_perfil_a=True, hoje=HOJE
        )
    assert bloqueado is False, motivo


@pytest.mark.django_db(transaction=True)
def test_carta_analise_liberadora_defasada_por_vi_nova_bloqueia():
    # Guard anti-stale: analise liberadora ANTERIOR a uma VI nova que reativou a
    # violacao nao libera — exige nova analise (INV-PAD-010).
    tenant = TenantFactory(slug=f"pq-stale-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    _insere_serie_tendencia(tenant, padrao)  # 7 VIs em jan/2026 (trend)
    with run_in_tenant_context(tenant.id):
        AnaliseCartaControle.objects.create(
            tenant=tenant,
            padrao=padrao,
            regra_violada=RegraWesternElectric.REGRA_5_TENDENCIA_7.value,
            pontos_referenciados_ids=[str(uuid4())],
            linha_central="4",
            ucl="10",
            lcl="-2",
            sigma="2",
            n_pontos=7,
            janela_meses=24,
            versao_motor_shewhart="shewhart-1.0.0",
            decisao_rt=DecisaoRTCarta.ACEITO_COM_JUSTIFICATIVA.value,
            justificativa_canonicalizada="tendencia aceita na epoca",
            justificativa_hash="v1$j",
        )
        # VI nova POSTERIOR a analise (data_vi no futuro relativo ao criado_em).
        VerificacaoIntermediaria.objects.create(
            tenant=tenant,
            padrao=padrao,
            data_vi=timezone.now() + timedelta(days=1),
            executor_id_hash="v1$e",
            metodo_canonicalizado="m",
            metodo_hash="v1$h",
            resultado=ResultadoVI.APROVADO.value,
            desvio_observado=Decimal("8"),
        )
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
            padrao.id, tenant_e_perfil_a=True, hoje=HOJE
        )
    assert bloqueado is True
    assert "defasada" in motivo


# --------------------------------------------------------------------------
# Cross-tenant (RLS) — padrao de outro tenant nao e visivel -> bloqueia
# --------------------------------------------------------------------------
@pytest.mark.django_db(transaction=True)
def test_cross_tenant_bloqueia():
    tenant_a = TenantFactory(slug=f"pq-ta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"pq-tb-{uuid4().hex[:6]}")
    padrao_a = _cria_padrao(tenant_a)
    # Avaliado no contexto do tenant B -> RLS esconde -> fail-closed.
    with run_in_tenant_context(tenant_b.id):
        bloqueado, motivo = query_service.padrao_bloqueado_para_uso(padrao_a.id, hoje=HOJE)
    assert bloqueado is True
    assert "inexistente" in motivo


# --------------------------------------------------------------------------
# snapshot_para_uso + buscar_disponivel
# --------------------------------------------------------------------------
@pytest.mark.django_db(transaction=True)
def test_snapshot_para_uso_monta_vo():
    tenant = TenantFactory(slug=f"pq-snap-{uuid4().hex[:6]}")
    padrao = _cria_padrao(tenant)
    with run_in_tenant_context(tenant.id):
        snap = query_service.snapshot_para_uso(padrao.id)
    assert snap is not None
    assert snap.padrao_id == padrao.id
    assert snap.numero_serie == padrao.numero_serie
    assert len(snap.incertezas_certificado) == 1
    assert snap.incertezas_certificado[0].valor == Decimal("0.001")


@pytest.mark.django_db(transaction=True)
def test_buscar_disponivel_filtra_bloqueados():
    tenant = TenantFactory(slug=f"pq-disp-{uuid4().hex[:6]}")
    ok = _cria_padrao(tenant)
    _cria_padrao(tenant, proximo_recal=date(2026, 1, 1))  # vencido
    _cria_padrao(tenant, rastreabilidade_origem_revogada=True)  # revogado
    with run_in_tenant_context(tenant.id):
        disponiveis = query_service.buscar_disponivel_para_calibracao(
            tenant.id, hoje=HOJE
        )
    assert ok.id in disponiveis
    assert len(disponiveis) == 1
