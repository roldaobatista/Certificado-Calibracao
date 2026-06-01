"""TST-004 — classes nomeando cada INV-CER (M8 Fatia 3 / T-CER-051 + T-CER-052).

Convenção do projeto (análoga `test_inv_proc_classes_nomeadas.py` do M7 e
`test_inv_ecmc_classes_nomeadas.py` do M6): todo INV crítico tem >=1 teste cujo
NOME cita o ID. Cada classe `TestINV_CER_*` exercita a barreira REAL — puro/Fake
onde a defesa é domínio/use case; PG-real onde é trigger/constraint; HTTP onde é
read-path (anti-reconsulta).

A `TestINV_CER_SNAPSHOT_CMC_001` consolida o teste anti-reconsulta (T-CER-052 /
TL-04): mock que FALHA se o read-path do cert emitido invocar `cmc_para`/
`tenant_perfil_e`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import DatabaseError
from src.application.metrologia.certificados.decidir_ponto_reconciliacao import (
    decidir_ponto_reconciliacao,
)
from src.application.metrologia.certificados.emitir_certificado import emitir_certificado
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
    TipoAcreditacao,
)
from src.domain.metrologia.certificados.erros import (
    CalibracaoNaoAprovadaError,
    OrcamentoPontoAmbiguoError,
    PadraoCalibracaoVencidaError,
    ReconciliacaoPendenteDecisaoRTError,
    RessalvaNaoRbcObrigatoriaError,
)
from src.domain.metrologia.certificados.numeracao import proximo_sequencial
from src.domain.metrologia.certificados.reconciliacao import reconciliar_pontos
from src.domain.metrologia.value_objects import Grandeza
from src.infrastructure.certificados.models import Certificado, StatusCertificado
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.regressao.test_inv_cer_p2_schema_triggers import _cenario as _cenario_pg
from tests.regressao.test_inv_cer_p2_schema_triggers import _emitir_real
from tests.test_m8_certificados_api_p2 import (
    _autenticar,
    _calibracao_com_ponto,
)
from tests.test_m8_certificados_api_p2 import (
    _cenario as _cenario_api,
)
from tests.test_m8_certificados_use_cases_p2 import (
    _DATA,
    _FAIXA,
    FakeAnaliseRepo,
    FakeCertRepo,
    FakeCmc,
    _calibracao,
    _decidir_input,
    _emitir_input,
    _orc,
    _pm,
)

_DBS = ["default", "breaker_writer"]
_VENCIDA = date(2026, 1, 1)


# ============================ domínio / use case (puro) ============================
class TestINV_CER_EMISSAO_001:
    def test_so_aprovada_emite(self):
        cal = _calibracao(status=EstadoCalibracao.RECEPCIONADA)
        inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=FakeCmc({Decimal("100"): Decimal("0.5")}))
        with pytest.raises(CalibracaoNaoAprovadaError):
            emitir_certificado(inp, cert_repo=FakeCertRepo(), analise_repo=FakeAnaliseRepo())


class TestINV_CER_RECONCILIA_001:
    def test_ponto_fora_da_declarada_nao_incluido(self):
        # ponto 2000 fora da faixa declarada 0..1000 → FORA_DECLARADA, não incluído.
        rec = reconciliar_pontos(
            pontos_medidos=[_pm("2000")], orcamentos_por_ponto=[_orc("2000", "0.8")],
            faixa_declarada=_FAIXA, grandeza=Grandeza.MASSA,
            cmc_para=None, data_emissao=_DATA, tenant_id=uuid4(),
        )
        p = rec.pontos[0]
        assert p.classificacao is ClassificacaoPonto.FORA_DECLARADA
        assert not p.incluido_no_certificado


class TestINV_CER_RECONCILIA_002:
    def test_u_menor_cmc_perfil_a_sem_decisao_bloqueia(self):
        cal = _calibracao()
        cmc = FakeCmc({Decimal("100"): Decimal("0.99")})  # CMC 0.99 > U 0.5 → U_MENOR_CMC
        inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.5")], perfil="A", cmc=cmc)
        with pytest.raises(ReconciliacaoPendenteDecisaoRTError):
            emitir_certificado(inp, cert_repo=FakeCertRepo(), analise_repo=FakeAnaliseRepo())


class TestINV_CER_RECONCILIA_003:
    def test_faixa_certificado_dos_validos(self):
        rec = reconciliar_pontos(
            pontos_medidos=[_pm("100"), _pm("500")], orcamentos_por_ponto=[_orc("100", "0.8"), _orc("500", "0.9")],
            faixa_declarada=_FAIXA, grandeza=Grandeza.MASSA, cmc_para=None, data_emissao=_DATA, tenant_id=uuid4(),
        )
        assert rec.faixa_certificado_min == Decimal("100")
        assert rec.faixa_certificado_max == Decimal("500")


class TestINV_CER_RECONCILIA_004:
    def test_pontos_ordenados_asc(self):
        # entra fora de ordem (500, 100) → sai ASC (100, 500) antes do hash/faixa.
        rec = reconciliar_pontos(
            pontos_medidos=[_pm("500"), _pm("100")], orcamentos_por_ponto=[_orc("500", "0.9"), _orc("100", "0.8")],
            faixa_declarada=_FAIXA, grandeza=Grandeza.MASSA, cmc_para=None, data_emissao=_DATA, tenant_id=uuid4(),
        )
        assert [p.ponto_calibracao for p in rec.pontos] == [Decimal("100"), Decimal("500")]


class TestINV_CER_RECONCILIA_005:
    def test_orcamento_duplicado_por_ponto_fail_closed(self):
        with pytest.raises(OrcamentoPontoAmbiguoError):
            reconciliar_pontos(
                pontos_medidos=[_pm("100")], orcamentos_por_ponto=[_orc("100", "0.8"), _orc("100", "0.9")],
                faixa_declarada=_FAIXA, grandeza=Grandeza.MASSA, cmc_para=None, data_emissao=_DATA, tenant_id=uuid4(),
            )


class TestINV_CER_NUM_002:
    def test_proximo_sequencial_denso_sem_buraco(self):
        # numero visível é denso (sem buraco); reusa o menor liberado.
        assert proximo_sequencial([1, 2, 3]) == 4
        assert proximo_sequencial([1, 3]) == 2  # reusa o 2 liberado


class TestINV_CER_PERFIL_001:
    def test_perfil_bcd_nunca_rbc(self):
        cal = _calibracao()
        inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="D", cmc=None)
        cert = emitir_certificado(inp, cert_repo=FakeCertRepo(), analise_repo=FakeAnaliseRepo())
        assert cert.tipo_acreditacao is TipoAcreditacao.NAO_RBC


class TestINV_CER_REGRA_DEC_001:
    def test_regra_decisao_congelada_no_snapshot(self):
        cal = _calibracao()
        inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=FakeCmc({Decimal("100"): Decimal("0.5")}))
        cert = emitir_certificado(inp, cert_repo=FakeCertRepo(), analise_repo=FakeAnaliseRepo())
        assert cert.regra_decisao_snapshot == {"regra_decisao": "ACEITACAO_SIMPLES"}


class TestINV_CER_CGCRE_VIG_001:
    def test_acreditacao_vencida_rebaixa_bloqueia_sem_decisao(self):
        cal = _calibracao()
        cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
        inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc, vigencia_fim=_VENCIDA)
        with pytest.raises(ReconciliacaoPendenteDecisaoRTError):
            emitir_certificado(inp, cert_repo=FakeCertRepo(), analise_repo=FakeAnaliseRepo())


class TestINV_CER_RESSALVA_001:
    def test_emitir_nao_rbc_sem_ressalva_bloqueia(self):
        with pytest.raises(RessalvaNaoRbcObrigatoriaError):
            decidir_ponto_reconciliacao(
                _decidir_input(uuid4(), "100", decisao_rt=DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO, categoria_motivo=CategoriaMotivoExclusao.OUTRO),
                analise_repo=FakeAnaliseRepo(),
            )


class TestINV_CER_PADRAO_VIG_001:
    def test_padrao_vencido_perfil_a_bloqueia(self):
        cal = _calibracao()
        cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
        inp = _emitir_input(
            cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc,
            padroes=[{"padrao_id": "p1", "calibracao_padrao_vigencia_fim": "2026-01-01"}],
        )
        with pytest.raises(PadraoCalibracaoVencidaError):
            emitir_certificado(inp, cert_repo=FakeCertRepo(), analise_repo=FakeAnaliseRepo())


# ============================ PG-real (trigger/constraint) ============================
@pytest.mark.django_db(transaction=True)
class TestINV_CER_NUM_001:
    def test_insert_fora_de_sequencia_bloqueia(self):
        from datetime import timedelta

        from django.utils import timezone
        from src.infrastructure.certificados.models import NumeroCertificadoReservado

        from tests.factories import TenantFactory

        tenant = TenantFactory(slug=f"invnum{uuid4().hex[:6]}")
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            NumeroCertificadoReservado.objects.create(
                tenant=tenant, tipo="CERTIFICADO", ano=2026, sequencial=5,
                ttl_expira_em=timezone.now() + timedelta(minutes=5),
            )


@pytest.mark.django_db(transaction=True)
class TestINV_CER_SNAPSHOT_PERFIL_001:
    def test_perfil_emissor_no_momento_persistido(self):
        tenant, equip = _cenario_pg("invperfil")
        cid, _ = _emitir_real(tenant, equip)
        with run_in_tenant_context(tenant.id):
            m = Certificado.all_objects.get(id=cid)
        assert m.perfil_emissor_no_momento == "A"  # NOT NULL no INSERT, imutável


@pytest.mark.django_db(transaction=True)
class TestINV_CER_WORM_001:
    def test_delete_de_cert_emitido_bloqueado(self):
        tenant, equip = _cenario_pg("invworm")
        cid, _ = _emitir_real(tenant, equip)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            Certificado.all_objects.filter(id=cid).delete()

    def test_tem_emitido_filtra_status_e_revogado(self):
        # TL-05: predicado explícito distingue emitido-vigente de revogado.
        tenant, equip = _cenario_pg("invtemem")
        cid, _ = _emitir_real(tenant, equip)
        with run_in_tenant_context(tenant.id):
            assert Certificado.all_objects.filter(
                id=cid, status=StatusCertificado.EMITIDO, revogado_em__isnull=True
            ).exists()


@pytest.mark.django_db(transaction=True, databases=_DBS)
class TestINV_CER_SNAPSHOT_CMC_001:
    """Anti-reconsulta (T-CER-052 / TL-04): o read-path do cert emitido lê SÓ o
    snapshot — mock que FALHA se `cmc_para`/`tenant_perfil_e` forem invocados."""

    def test_retrieve_nao_reconsulta_cmc_nem_perfil(self):
        c = _cenario_api(perfil_a=True)
        from tests.m8_pg_fixtures import criar_escopo_cmc_confirmado

        criar_escopo_cmc_confirmado(c["tenant"], cmc_valor=Decimal("0.5"))
        cal = _calibracao_com_ponto(c["tenant"], c["equip"], U="0.8")
        from rest_framework.test import APIClient

        client = APIClient()
        _autenticar(client, c["admin"], c["tenant"])
        emt = client.post(
            "/api/v1/certificados/emitir/",
            {"calibracao_id": str(cal.id), "correlation_id": str(uuid4())},
            format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        assert emt.status_code == 201, emt.content
        cert_id = emt.json()["id"]
        # Mocks que estouram se o read-path reconsultar (WORM furado por LEITURA).
        with patch(
            "src.infrastructure.metrologia.certificados.query_service.cmc_para_adapter",
            side_effect=AssertionError("read-path reconsultou cmc_para!"),
        ) as m_cmc, patch(
            "src.infrastructure.authz.perfil_tenant_helper.tenant_perfil_e",
            side_effect=AssertionError("read-path reconsultou tenant_perfil_e!"),
        ) as m_perfil:
            g = client.get(f"/api/v1/certificados/{cert_id}/")
        assert g.status_code == 200, g.content
        m_cmc.assert_not_called()
        m_perfil.assert_not_called()
        # cmc exibido é o do SNAPSHOT (congelado), não reconsultado.
        assert Decimal(g.json()["pontos"][0]["cmc_no_ponto"]) == Decimal("0.5")
        assert g.json()["status"] == EstadoCertificado.EMITIDO.value
