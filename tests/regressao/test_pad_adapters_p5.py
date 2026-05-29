"""M5 P5 — adapters Django (repositories.py) round-trip PG-real.

Exercita o stack completo use case -> adapter -> PG em contexto de tenant.
Foco critico: o fluxo de recal aprovado atualiza as incertezas do padrao via
`aplicar_recal_aprovado` (GUC app.padrao_recal_em_curso) — prova que INV-PAD-006
deixa o caminho legitimo passar (e os testes P2 ja provaram que UPDATE direto
fora desse caminho e bloqueado).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.application.metrologia.padroes import (
    aprovar_recal_rt,
    cadastrar_padrao,
    registrar_recal_envio,
    registrar_recal_retorno,
    registrar_verificacao_intermediaria,
    revogar_rastreabilidade_origem,
)
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    EstadoPadrao,
    ResultadoVI,
    StatusRecal,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)
from src.infrastructure.metrologia.padroes.repositories import (
    DjangoPadraoRepository,
    DjangoRecalExternoRepository,
    DjangoVerificacaoIntermediariaRepository,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _cadastrar_input(tenant_id, **kw):
    base = {
        "tenant_id": tenant_id,
        "numero_serie": f"PAD-{uuid4().hex[:8]}",
        "fabricante": "Mettler",
        "modelo": "XPR",
        "subtipo": SubtipoPadrao.PRINCIPAL,
        "grandezas": (Grandeza.MASSA,),
        "faixas": (FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),),
        "incertezas_certificado": (
            IncertezaExpandida(Decimal("0.001"), Decimal("2"), Decimal("0.9545"), "g"),
        ),
        "vinculacao": VinculacaoCadeia.INMETRO,
        "classe": ClassePadrao.E2,
        "cert_externo_storage_key": "key-1",
        "validade_certificado_rastreabilidade": date(2027, 1, 1),
        "proximo_recal": date(2027, 1, 1),
        "intervalo_recal_meses": 12,
        "intervalo_vi_meses": 3,
        "criterio_intervalo": "cl. 6.4.7 historico de estabilidade",
        "vigencia_inicio": datetime(2026, 5, 1, tzinfo=UTC),
        "correlation_id": uuid4(),
        "tenant_e_perfil_a": True,
    }
    base.update(kw)
    return cadastrar_padrao.CadastrarPadraoInput(**base)


@pytest.mark.django_db(transaction=True)
def test_cadastrar_e_obter_round_trip_vos():
    tenant = TenantFactory(slug=f"ad-rt-{uuid4().hex[:6]}")
    repo = DjangoPadraoRepository()
    with run_in_tenant_context(tenant.id):
        out = cadastrar_padrao.executar(_cadastrar_input(tenant.id), repo)
        lido = repo.obter_por_id(out.snapshot.id)
    assert lido is not None
    # VOs round-trip (JSON -> VO) sem perda
    assert lido.grandezas == (Grandeza.MASSA,)
    assert lido.faixas[0].superior == Decimal("1000")
    assert lido.incertezas_certificado[0].valor == Decimal("0.001")
    assert lido.estado == EstadoPadrao.EM_USO


@pytest.mark.django_db(transaction=True)
def test_inv_pad_001_existe_numero_serie():
    tenant = TenantFactory(slug=f"ad-ns-{uuid4().hex[:6]}")
    repo = DjangoPadraoRepository()
    with run_in_tenant_context(tenant.id):
        out = cadastrar_padrao.executar(_cadastrar_input(tenant.id), repo)
        assert repo.existe_numero_serie(tenant.id, out.snapshot.numero_serie) is True
        assert repo.existe_numero_serie(tenant.id, "NAO-EXISTE") is False


@pytest.mark.django_db(transaction=True)
def test_fluxo_recal_aprovado_atualiza_incertezas_via_guc():
    """Stack completo: cadastrar -> envio -> retorno -> aprovar; incertezas do
    padrao em PG batem com as do recal (aplicar_recal_aprovado + GUC)."""
    tenant = TenantFactory(slug=f"ad-recal-{uuid4().hex[:6]}")
    rp, rr = DjangoPadraoRepository(), DjangoRecalExternoRepository()
    nova_inc = (
        IncertezaExpandida(Decimal("0.0005"), Decimal("2"), Decimal("0.9545"), "g"),
    )
    with run_in_tenant_context(tenant.id):
        padrao = cadastrar_padrao.executar(_cadastrar_input(tenant.id), rp).snapshot
        recal = registrar_recal_envio.executar(
            registrar_recal_envio.RegistrarRecalEnvioInput(
                tenant_id=tenant.id,
                padrao_id=padrao.id,
                enviado_em=datetime(2026, 6, 1, tzinfo=UTC),
                lab_externo="Lab RBC",
                responsavel_envio_id_hash="v1$resp",
            ),
            rp,
            rr,
        ).recal
        registrar_recal_retorno.executar(
            registrar_recal_retorno.RegistrarRecalRetornoInput(
                tenant_id=tenant.id,
                recal_id=recal.id,
                status=StatusRecal.RETORNADO,
                retornado_em=datetime(2026, 7, 1, tzinfo=UTC),
                incertezas_novas=nova_inc,
                validade_nova=date(2028, 7, 1),
                valor_convencional_novo=Decimal("1.0"),
            ),
            rp,
            rr,
        )
        out = aprovar_recal_rt.executar(
            aprovar_recal_rt.AprovarRecalRTInput(
                tenant_id=tenant.id,
                recal_id=recal.id,
                aprovado=True,
                aprovado_rt_id_hash="v1$rt",
                decidido_em=datetime(2026, 7, 2, tzinfo=UTC),
                proximo_recal_novo=date(2028, 6, 1),
            ),
            rp,
            rr,
        )
        assert out.padrao.estado == EstadoPadrao.EM_USO
        lido = rp.obter_por_id(padrao.id)
    # GUC liberou o UPDATE das incertezas (INV-PAD-006 caminho legitimo).
    assert lido is not None
    assert lido.incertezas_certificado[0].valor == Decimal("0.0005")
    assert lido.validade_certificado_rastreabilidade == date(2028, 7, 1)
    assert lido.proximo_recal == date(2028, 6, 1)


@pytest.mark.django_db(transaction=True)
def test_revogar_rastreabilidade_via_atualizar_com_lock_sem_guc():
    """atualizar_com_lock muda flag/estado SEM tocar incertezas (sem GUC)."""
    tenant = TenantFactory(slug=f"ad-rev-{uuid4().hex[:6]}")
    rp = DjangoPadraoRepository()
    with run_in_tenant_context(tenant.id):
        padrao = cadastrar_padrao.executar(_cadastrar_input(tenant.id), rp).snapshot
        out = revogar_rastreabilidade_origem.executar(
            revogar_rastreabilidade_origem.RevogarRastreabilidadeInput(
                tenant_id=tenant.id,
                padrao_id=padrao.id,
                motivo="origem perdeu acreditacao CGCRE",
            ),
            rp,
        )
        lido = rp.obter_por_id(padrao.id)
    assert out.padrao.rastreabilidade_origem_revogada is True
    assert lido is not None
    assert lido.rastreabilidade_origem_revogada is True
    assert lido.revision == 1


@pytest.mark.django_db(transaction=True)
def test_cas_conflito_revision_retorna_false():
    tenant = TenantFactory(slug=f"ad-cas-{uuid4().hex[:6]}")
    rp = DjangoPadraoRepository()
    with run_in_tenant_context(tenant.id):
        padrao = cadastrar_padrao.executar(_cadastrar_input(tenant.id), rp).snapshot
        from dataclasses import replace

        # revision_anterior errado (5) -> CAS nao casa -> False
        ok = rp.atualizar_com_lock(replace(padrao, revision=6), revision_anterior=5)
    assert ok is False


@pytest.mark.django_db(transaction=True)
def test_vi_salvar_e_listar_ordenado():
    tenant = TenantFactory(slug=f"ad-vi-{uuid4().hex[:6]}")
    rp, rv = DjangoPadraoRepository(), DjangoVerificacaoIntermediariaRepository()
    with run_in_tenant_context(tenant.id):
        padrao = cadastrar_padrao.executar(_cadastrar_input(tenant.id), rp).snapshot
        for dia in (3, 1, 2):
            registrar_verificacao_intermediaria.executar(
                registrar_verificacao_intermediaria.RegistrarVIInput(
                    tenant_id=tenant.id,
                    padrao_id=padrao.id,
                    data_vi=datetime(2026, 5, dia, tzinfo=UTC),
                    executor_id_hash="v1$e",
                    metodo_canonicalizado="comparacao",
                    metodo_hash="v1$h",
                    resultado=ResultadoVI.APROVADO,
                    tenant_e_perfil_a=False,
                ),
                rp,
                rv,
            )
        vis = rv.listar_por_padrao(padrao.id)
    assert [v.data_vi.day for v in vis] == [1, 2, 3]  # ordenado por data_vi


@pytest.mark.django_db(transaction=True)
def test_pt_adapter_round_trip_e_resultado():
    from src.domain.metrologia.padroes.entities import IntercomparacaoPTSnapshot
    from src.domain.metrologia.padroes.enums import ResultadoPT
    from src.infrastructure.metrologia.padroes.repositories import (
        DjangoIntercomparacaoPTRepository,
    )

    tenant = TenantFactory(slug=f"ad-pt-{uuid4().hex[:6]}")
    rp, rpt = DjangoPadraoRepository(), DjangoIntercomparacaoPTRepository()
    pt_id = uuid4()
    with run_in_tenant_context(tenant.id):
        padrao = cadastrar_padrao.executar(_cadastrar_input(tenant.id), rp).snapshot
        rpt.salvar_nova(
            IntercomparacaoPTSnapshot(
                id=pt_id,
                tenant_id=tenant.id,
                padrao_id=padrao.id,
                lab_organizador="INMETRO",
                protocolo="PT-1",
                data_inicio=datetime(2026, 4, 1, tzinfo=UTC),
            )
        )
        lido = rpt.obter_por_id(pt_id)
        assert lido is not None
        assert lido.resultado is None
        rpt.atualizar_resultado(
            __import__("dataclasses").replace(
                lido,
                resultado=ResultadoPT.APROVADO,
                data_resultado=datetime(2026, 5, 1, tzinfo=UTC),
                zeta_score=Decimal("0.5"),
            )
        )
        relido = rpt.obter_por_id(pt_id)
    assert relido is not None
    assert relido.resultado == ResultadoPT.APROVADO
    assert relido.zeta_score == Decimal("0.5")


@pytest.mark.django_db(transaction=True)
def test_analise_carta_adapter_salvar_e_listar():
    from src.domain.metrologia.padroes.entities import AnaliseCartaControleSnapshot
    from src.domain.metrologia.padroes.enums import (
        DecisaoRTCarta,
        RegraWesternElectric,
    )
    from src.infrastructure.metrologia.padroes.repositories import (
        DjangoAnaliseCartaControleRepository,
    )

    tenant = TenantFactory(slug=f"ad-acc-{uuid4().hex[:6]}")
    rp, ra = DjangoPadraoRepository(), DjangoAnaliseCartaControleRepository()
    ponto = uuid4()
    with run_in_tenant_context(tenant.id):
        padrao = cadastrar_padrao.executar(_cadastrar_input(tenant.id), rp).snapshot
        ra.salvar_nova(
            AnaliseCartaControleSnapshot(
                id=uuid4(),
                tenant_id=tenant.id,
                padrao_id=padrao.id,
                regra_violada=RegraWesternElectric.REGRA_5_TENDENCIA_7,
                pontos_referenciados_ids=(ponto,),
                linha_central=Decimal("4"),
                ucl=Decimal("10"),
                lcl=Decimal("-2"),
                sigma=Decimal("2"),
                n_pontos=7,
                janela_meses=24,
                versao_motor_shewhart="shewhart-1.0.0",
                decisao_rt=DecisaoRTCarta.RECALIBRAR,
                justificativa_canonicalizada="tendencia — recalibrar",
                justificativa_hash="v1$j",
                criado_em=datetime(2026, 5, 1, tzinfo=UTC),
            )
        )
        analises = ra.listar_por_padrao(padrao.id)
    assert len(analises) == 1
    assert analises[0].decisao_rt == DecisaoRTCarta.RECALIBRAR
    assert analises[0].pontos_referenciados_ids == (ponto,)


@pytest.mark.django_db(transaction=True)
def test_vinculo_auxiliar_adapter_salvar_e_listar_vigentes():
    from src.domain.metrologia.padroes.entities import VinculoAuxiliarSnapshot
    from src.infrastructure.metrologia.padroes.repositories import (
        DjangoVinculoAuxiliarRepository,
    )

    tenant = TenantFactory(slug=f"ad-vinc-{uuid4().hex[:6]}")
    rp, rvinc = DjangoPadraoRepository(), DjangoVinculoAuxiliarRepository()
    with run_in_tenant_context(tenant.id):
        principal = cadastrar_padrao.executar(_cadastrar_input(tenant.id), rp).snapshot
        auxiliar = cadastrar_padrao.executar(
            _cadastrar_input(
                tenant.id, subtipo=SubtipoPadrao.AUXILIAR_AMBIENTAL
            ),
            rp,
        ).snapshot
        rvinc.salvar_novo(
            VinculoAuxiliarSnapshot(
                id=uuid4(),
                tenant_id=tenant.id,
                padrao_principal_id=principal.id,
                padrao_auxiliar_id=auxiliar.id,
                grandeza_influencia=Grandeza.TEMPERATURA,
                vigencia_inicio=datetime(2026, 5, 1, tzinfo=UTC),
            )
        )
        vigentes = rvinc.listar_auxiliares_vigentes_de(principal.id)
    assert len(vigentes) == 1
    assert vigentes[0].grandeza_influencia == Grandeza.TEMPERATURA
    assert vigentes[0].padrao_auxiliar_id == auxiliar.id
