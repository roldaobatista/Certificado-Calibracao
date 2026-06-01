"""M8 Fatia 2 (T-CER-040..043) — use cases decidir_ponto + emitir_certificado.

PUROS (Fakes in-memory, sem Django/PG): exercitam a orquestração de domínio —
reconciliação + decisão WORM do RT + completude perfil-aware + tipo RBC/NÃO-RBC +
fail-closed (calibração não aprovada / faixa ausente / pendência de decisão / abort).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from src.application.metrologia.certificados.decidir_ponto_reconciliacao import (
    DecidirPontoInput,
    decidir_ponto_reconciliacao,
)
from src.application.metrologia.certificados.emitir_certificado import (
    EmitirCertificadoInput,
    emitir_certificado,
)
from src.application.metrologia.certificados.reemitir_certificado import (
    ReemitirCertificadoInput,
    reemitir_certificado,
)
from src.domain.metrologia.calibracao.entities import OrcamentoPorPontoSnapshot
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    LeiEscalonamento,
    MetodoTipoAPonto,
)
from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
    TipoAcreditacao,
)
from src.domain.metrologia.certificados.erros import (
    CalibracaoNaoAprovadaError,
    CategoriaIncoerenteError,
    CertificadoJaEmitidoError,
    EmissaoAbortadaPeloRTError,
    FaixaDeclaradaAusenteError,
    JustificativaInsuficienteError,
    MotivoReemissaoInsuficienteError,
    PadraoCalibracaoVencidaError,
    ReconciliacaoPendenteDecisaoRTError,
    ReemissaoConflitanteError,
    RessalvaNaoRbcObrigatoriaError,
)
from src.domain.metrologia.certificados.reconciliacao import PontoMedido
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

_TENANT = uuid4()
_DATA = date(2026, 5, 31)
_NOW = datetime(2026, 5, 31, 12, 0, tzinfo=UTC)
_FAIXA = FaixaMedicao(Decimal("0"), Decimal("1000"), "g")


# --- Fakes --------------------------------------------------------------------


class FakeAnaliseRepo:
    def __init__(self):
        self.dados = {}  # (calibracao_id, ponto) -> decisao

    def salvar_decisao(self, d):
        self.dados[(d.calibracao_id, d.ponto_calibracao)] = d

    def listar_por_calibracao(self, *, tenant_id, calibracao_id):
        return [d for (c, _p), d in self.dados.items() if c == calibracao_id]

    def existe_decisao_para_ponto(self, *, tenant_id, calibracao_id, ponto_calibracao):
        return (calibracao_id, ponto_calibracao) in self.dados

    def obter_decisao_por_ponto(self, *, tenant_id, calibracao_id):
        return {p: d for (c, p), d in self.dados.items() if c == calibracao_id}


class FakeCertRepo:
    def __init__(self):
        self.certs = {}
        self.pontos = {}
        self.seq = 0
        self.marcar_ok = True  # CAS configurável (False ⇒ corrida/409)
        self.substituidas = []  # (certificado_id, revision_anterior)

    def obter_por_id(self, certificado_id):
        return self.certs.get(certificado_id)

    def existe_chave(self, *, tenant_id, calibracao_id, versao):
        return any(c.calibracao_id == calibracao_id and c.versao == versao for c in self.certs.values())

    def proximo_numero_interno(self, *, tenant_id):
        self.seq += 1
        return self.seq

    def salvar_novo(self, cert, pontos):
        self.certs[cert.id] = cert
        self.pontos[cert.id] = list(pontos)

    def marcar_substituida(self, *, certificado_id, revision_anterior):
        self.substituidas.append((certificado_id, revision_anterior))
        return self.marcar_ok


class FakeCmc:
    def __init__(self, mapa):
        self.mapa = mapa

    def __call__(self, *, tenant_id, grandeza, ponto, data):
        return self.mapa.get(ponto)


# --- helpers ------------------------------------------------------------------


def _calibracao(*, status=EstadoCalibracao.APROVADA, grandeza=Grandeza.MASSA, faixa=_FAIXA, cal_id=None):
    return SimpleNamespace(
        id=cal_id or uuid4(),
        status=status,
        grandeza_calibrada=grandeza,
        faixa_calibrada_declarada=faixa,
        instrumento_id=uuid4(),
        snapshot_equipamento_json={"tag": "BAL-01"},
        cliente_referencia_hash="v01$cli",
        regra_decisao=SimpleNamespace(value="ACEITACAO_SIMPLES"),
    )


def _orc(ponto, u):
    return OrcamentoPorPontoSnapshot(
        id=uuid4(), tenant_id=_TENANT, orcamento_incerteza_id=uuid4(),
        ponto_calibracao=Decimal(ponto), u_combinada_no_ponto=Decimal(u) / Decimal("2"),
        U_expandida_no_ponto=Decimal(u), k_no_ponto=Decimal("2"),
        nivel_confianca_no_ponto=Decimal("0.9545"), grau_liberdade_efetivo_no_ponto=Decimal("60"),
        replay_determinismo_hash_no_ponto="v01$x", metodo_tipo_a_ponto=MetodoTipoAPonto.SX_PROPRIO,
        n_repeticoes_ponto=10, lei_escalonamento_aplicada=LeiEscalonamento.CONSTANTE,
    )


def _pm(ponto):
    return PontoMedido(ponto_calibracao=Decimal(ponto), valor_reportado=Decimal(ponto), unidade="g")


def _emitir_input(
    cal, *, pontos, orcs, perfil, cmc, versao=1,
    vigencia_fim=None, suspensa_em=None, suspensa_ate=None, padroes=None, versao_anterior_id=None,
):
    return EmitirCertificadoInput(
        tenant_id=_TENANT, calibracao=cal, pontos_medidos=pontos, orcamentos_por_ponto=orcs,
        perfil=perfil, numero_interno=1, numero_certificado="BALANCAS-2026-000001",
        snapshot_padroes_usados_json=padroes if padroes is not None else [{"padrao_id": "p1"}],
        data_emissao=_DATA, emitido_em=_NOW, correlation_id=uuid4(), cmc_para=cmc,
        acreditacao_vigencia_fim=vigencia_fim,
        acreditacao_suspensa_em=suspensa_em, acreditacao_suspensa_ate=suspensa_ate,
        versao=versao, versao_anterior_id=versao_anterior_id,
    )


# =============================================================
# Fatia 2a — decidir_ponto_reconciliacao
# =============================================================


def _decidir_input(cal_id, ponto, **kw):
    base = {
        "tenant_id": _TENANT,
        "calibracao_id": cal_id,
        "ponto_calibracao": Decimal(ponto),
        "classificacao": ClassificacaoPonto.U_MENOR_CMC,
        "decisao_rt": DecisaoReconciliacaoRT.EXCLUIR_PONTO,
        "categoria_motivo": CategoriaMotivoExclusao.U_MAIOR_QUE_CMC_BUG,
        "justificativa": "ponto excluido por bug de cmc otimista demais perante a U real",
        "correlation_id": uuid4(),
        "criado_em": _NOW,
    }
    return DecidirPontoInput(**{**base, **kw})


def test_decidir_ponto_crava_decisao():
    repo = FakeAnaliseRepo()
    cal_id = uuid4()
    d = decidir_ponto_reconciliacao(_decidir_input(cal_id, "100"), analise_repo=repo)
    assert d.decisao_rt is DecisaoReconciliacaoRT.EXCLUIR_PONTO
    assert d.justificativa_hash.startswith("v01$")
    assert repo.existe_decisao_para_ponto(tenant_id=_TENANT, calibracao_id=cal_id, ponto_calibracao=Decimal("100"))


def test_decidir_ponto_idempotente():
    repo = FakeAnaliseRepo()
    cal_id = uuid4()
    d1 = decidir_ponto_reconciliacao(_decidir_input(cal_id, "100"), analise_repo=repo)
    d2 = decidir_ponto_reconciliacao(_decidir_input(cal_id, "100"), analise_repo=repo)
    assert d1.id == d2.id  # replay, não duplica
    assert len(repo.dados) == 1


def test_decidir_ponto_categoria_incoerente():
    repo = FakeAnaliseRepo()
    with pytest.raises(CategoriaIncoerenteError):
        decidir_ponto_reconciliacao(
            _decidir_input(uuid4(), "100", categoria_motivo=CategoriaMotivoExclusao.PONTO_FORA_FAIXA_DECLARADA),
            analise_repo=repo,
        )


def test_decidir_ponto_emitir_nao_rbc_exige_ressalva():
    repo = FakeAnaliseRepo()
    with pytest.raises(RessalvaNaoRbcObrigatoriaError):
        decidir_ponto_reconciliacao(
            _decidir_input(uuid4(), "100", decisao_rt=DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO, categoria_motivo=CategoriaMotivoExclusao.OUTRO),
            analise_repo=repo,
        )


def test_decidir_ponto_justificativa_curta():
    repo = FakeAnaliseRepo()
    with pytest.raises(JustificativaInsuficienteError):
        decidir_ponto_reconciliacao(_decidir_input(uuid4(), "100", justificativa="curta"), analise_repo=repo)


# =============================================================
# Fatia 2b — emitir_certificado
# =============================================================


def test_emitir_rbc_feliz_perfil_a():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5"), Decimal("500"): Decimal("0.5")})
    inp = _emitir_input(cal, pontos=[_pm("100"), _pm("500")], orcs=[_orc("100", "0.8"), _orc("500", "0.9")], perfil="A", cmc=cmc)
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.RBC
    assert cert.status is EstadoCertificado.EMITIDO
    assert cert.faixa_certificado_min == Decimal("100")
    assert cert.faixa_certificado_max == Decimal("500")
    assert cert.reconciliacao_hash.startswith("v01$")
    assert len(cert_repo.pontos[cert.id]) == 2


def test_emitir_calibracao_nao_aprovada():
    cal = _calibracao(status=EstadoCalibracao.EM_REVISAO_1) if hasattr(EstadoCalibracao, "EM_REVISAO_1") else _calibracao(status=EstadoCalibracao.RECEPCIONADA)
    inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=FakeCmc({Decimal("100"): Decimal("0.5")}))
    with pytest.raises(CalibracaoNaoAprovadaError):
        emitir_certificado(inp, cert_repo=FakeCertRepo(), analise_repo=FakeAnaliseRepo())


def test_emitir_faixa_declarada_ausente():
    cal = _calibracao(grandeza=None, faixa=None)
    inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=FakeCmc({}))
    with pytest.raises(FaixaDeclaradaAusenteError):
        emitir_certificado(inp, cert_repo=FakeCertRepo(), analise_repo=FakeAnaliseRepo())


def test_emitir_perfil_a_ponto_nao_rbc_sem_decisao_bloqueia_sem_persistir():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    # ponto 100 RBC_OK; ponto 500 U<CMC (não-RBC) sem decisão → bloqueia
    cmc = FakeCmc({Decimal("100"): Decimal("0.5"), Decimal("500"): Decimal("0.99")})
    inp = _emitir_input(cal, pontos=[_pm("100"), _pm("500")], orcs=[_orc("100", "0.8"), _orc("500", "0.5")], perfil="A", cmc=cmc)
    with pytest.raises(ReconciliacaoPendenteDecisaoRTError):
        emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert_repo.certs == {}  # nada persistido


def test_emitir_com_decisao_excluir_ponto():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5"), Decimal("500"): Decimal("0.99")})
    decidir_ponto_reconciliacao(_decidir_input(cal.id, "500"), analise_repo=analise_repo)
    inp = _emitir_input(cal, pontos=[_pm("100"), _pm("500")], orcs=[_orc("100", "0.8"), _orc("500", "0.5")], perfil="A", cmc=cmc)
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    pts = {p.ponto_calibracao: p for p in cert_repo.pontos[cert.id]}
    assert pts[Decimal("500")].classificacao is ClassificacaoPonto.EXCLUIDO
    assert not pts[Decimal("500")].incluido_no_certificado
    # faixa só do ponto válido (100)
    assert cert.faixa_certificado_max == Decimal("100")


def test_emitir_com_decisao_emitir_nao_rbc_grava_ressalva():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5"), Decimal("500"): Decimal("0.99")})
    decidir_ponto_reconciliacao(
        _decidir_input(cal.id, "500", decisao_rt=DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO,
                       categoria_motivo=CategoriaMotivoExclusao.OUTRO,
                       ressalva_nao_rbc="ponto nao coberto pela acreditacao RBC"),
        analise_repo=analise_repo,
    )
    inp = _emitir_input(cal, pontos=[_pm("100"), _pm("500")], orcs=[_orc("100", "0.8"), _orc("500", "0.5")], perfil="A", cmc=cmc)
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    pts = {p.ponto_calibracao: p for p in cert_repo.pontos[cert.id]}
    assert pts[Decimal("500")].incluido_no_certificado
    assert pts[Decimal("500")].ressalva_nao_rbc.startswith("ponto nao coberto")


def test_emitir_perfil_bcd_nao_rbc():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    inp = _emitir_input(cal, pontos=[_pm("100"), _pm("500")], orcs=[_orc("100", "0.8"), _orc("500", "0.9")], perfil="D", cmc=None)
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.NAO_RBC
    assert len(cert_repo.pontos[cert.id]) == 2  # todos reportados (não-RBC)


def test_emitir_idempotencia_dupla_emissao():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc)
    emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    with pytest.raises(CertificadoJaEmitidoError):
        emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)


def test_emitir_abortar_pelo_rt():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5"), Decimal("500"): Decimal("0.99")})
    decidir_ponto_reconciliacao(
        _decidir_input(cal.id, "500", decisao_rt=DecisaoReconciliacaoRT.ABORTAR, categoria_motivo=CategoriaMotivoExclusao.OUTRO),
        analise_repo=analise_repo,
    )
    inp = _emitir_input(cal, pontos=[_pm("100"), _pm("500")], orcs=[_orc("100", "0.8"), _orc("500", "0.5")], perfil="A", cmc=cmc)
    with pytest.raises(EmissaoAbortadaPeloRTError):
        emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert_repo.certs == {}


# =============================================================
# Fatia 2b — INV-CER-CGCRE-VIG-001 (acreditação vencida/suspensa rebaixa RBC→não-RBC)
# =============================================================

_VENCIDA = date(2026, 1, 1)  # < _DATA (2026-05-31)
_VIGENTE = date(2027, 1, 1)  # > _DATA


def test_cgcre_vigencia_none_fail_open_lazy_emite_rbc():
    # Campo novo não populado (default None) ⇒ fail-open lazy ⇒ RBC normal.
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(_calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc)
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.RBC


def test_cgcre_vigente_emite_rbc():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(_calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc, vigencia_fim=_VIGENTE)
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.RBC


def test_cgcre_vencida_perfil_a_sem_decisao_bloqueia():
    # Vencida ⇒ rebaixa cmc→None ⇒ ponto vira não-RBC ⇒ perfil A exige decisão RT.
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(_calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc, vigencia_fim=_VENCIDA)
    with pytest.raises(ReconciliacaoPendenteDecisaoRTError):
        emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert_repo.certs == {}  # nada persistido (fail-closed)


def test_cgcre_suspensa_rebaixa_bloqueia():
    # Suspensão cobre a data de emissão (fail-closed imediato), mesmo com vigência None.
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(
        _calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc,
        suspensa_em=date(2026, 5, 1), suspensa_ate=date(2026, 6, 30),  # cobre _DATA=2026-05-31
    )
    with pytest.raises(ReconciliacaoPendenteDecisaoRTError):
        emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert_repo.certs == {}


def test_cgcre_suspensao_futura_nao_rebaixa_emite_rbc():
    # Suspensão começa DEPOIS da data de emissão → não cobre → RBC normal.
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(
        _calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc,
        suspensa_em=date(2026, 7, 1), suspensa_ate=date(2026, 8, 1),  # após _DATA
    )
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.RBC


def test_cgcre_vigencia_igual_data_emissao_ainda_vigente():
    # Borda: vigência == data de emissão ⇒ válido no último dia (>=) ⇒ RBC.
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(_calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc, vigencia_fim=_DATA)
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.RBC


def test_cgcre_vencida_perfil_a_com_decisao_emite_nao_rbc():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    # Rebaixado a SEM_CMC; RT decide reportar não-RBC com ressalva.
    decidir_ponto_reconciliacao(
        _decidir_input(
            cal.id, "100", classificacao=ClassificacaoPonto.SEM_CMC,
            decisao_rt=DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO,
            categoria_motivo=CategoriaMotivoExclusao.OUTRO,
            ressalva_nao_rbc="ponto reportado sem selo RBC: acreditacao vencida na emissao",
        ),
        analise_repo=analise_repo,
    )
    inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc, vigencia_fim=_VENCIDA)
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.NAO_RBC


# =============================================================
# Fatia 2b — INV-CER-PADRAO-VIG-001 (padrão com calibração vencida — cl. 6.5 / NC-07)
# =============================================================


def test_padrao_vencido_perfil_a_bloqueia():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(
        _calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc,
        padroes=[{"padrao_id": "p1", "calibracao_padrao_vigencia_fim": "2026-01-01"}],
    )
    with pytest.raises(PadraoCalibracaoVencidaError):
        emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert_repo.certs == {}


def test_padrao_vencido_perfil_d_nao_bloqueia():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    inp = _emitir_input(
        _calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="D", cmc=None,
        padroes=[{"padrao_id": "p1", "calibracao_padrao_vigencia_fim": "2026-01-01"}],
    )
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.NAO_RBC


def test_padrao_vigente_perfil_a_emite_rbc():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(
        _calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc,
        padroes=[{"padrao_id": "p1", "calibracao_padrao_vigencia_fim": "2027-01-01"}],
    )
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.RBC


def test_padrao_vigencia_igual_data_emissao_nao_bloqueia():
    # Borda: padrão vence EXATAMENTE na data de emissão ⇒ válido no dia (vig < emissão é False).
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(
        _calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc,
        padroes=[{"padrao_id": "p1", "calibracao_padrao_vigencia_fim": _DATA.isoformat()}],
    )
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.RBC


def test_padrao_vigencia_malformada_fail_open():
    # Coerção tolerante: vigência malformada no snapshot ⇒ tratada como ausente (não bloqueia).
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    inp = _emitir_input(
        _calibracao(), pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc,
        padroes=[{"padrao_id": "p1", "calibracao_padrao_vigencia_fim": "data-invalida"}],
    )
    cert = emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)
    assert cert.tipo_acreditacao is TipoAcreditacao.RBC


# =============================================================
# Fatia 2b — reemitir_certificado (v(N+1) + v(N)→SUBSTITUIDA — US-CER-004)
# =============================================================

_MOTIVO_OK = "correcao de metadado do certificado a pedido formal do cliente conforme NC registrada"


def _emitir_v1(cert_repo, analise_repo, cal, cmc):
    inp = _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc)
    return emitir_certificado(inp, cert_repo=cert_repo, analise_repo=analise_repo)


def _reemitir_input(v1, cal, *, perfil, cmc, motivo, revision=0):
    return ReemitirCertificadoInput(
        tenant_id=_TENANT, certificado_anterior=v1, revision_anterior=revision, motivo=motivo,
        calibracao=cal, pontos_medidos=[_pm("100")], orcamentos_por_ponto=[_orc("100", "0.8")],
        perfil=perfil, numero_interno=2, numero_certificado="BALANCAS-2026-000002",
        data_emissao=_DATA, emitido_em=_NOW, correlation_id=uuid4(), cmc_para=cmc,
    )


def test_reemitir_cria_v2_substitui_v1():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    v1 = _emitir_v1(cert_repo, analise_repo, cal, cmc)
    v2 = reemitir_certificado(
        _reemitir_input(v1, cal, perfil="A", cmc=cmc, motivo=_MOTIVO_OK),
        cert_repo=cert_repo, analise_repo=analise_repo,
    )
    assert v2.versao == 2
    assert v2.versao_anterior_id == v1.id
    assert (v1.id, 0) in cert_repo.substituidas  # CAS chamado no anterior


def test_reemitir_herda_snapshot_padroes_do_anterior():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    v1 = _emitir_v1(cert_repo, analise_repo, cal, cmc)
    v2 = reemitir_certificado(
        _reemitir_input(v1, cal, perfil="A", cmc=cmc, motivo=_MOTIVO_OK),
        cert_repo=cert_repo, analise_repo=analise_repo,
    )
    assert v2.snapshot_padroes_usados_json == v1.snapshot_padroes_usados_json


def test_reemitir_herda_lista_padroes_vazia():
    # Borda M2 (tech-lead): v(N) com snapshot_padroes=[] ⇒ reemissão herda [] (≠ None sentinela).
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    v1 = emitir_certificado(
        _emitir_input(cal, pontos=[_pm("100")], orcs=[_orc("100", "0.8")], perfil="A", cmc=cmc, padroes=[]),
        cert_repo=cert_repo, analise_repo=analise_repo,
    )
    v2 = reemitir_certificado(
        _reemitir_input(v1, cal, perfil="A", cmc=cmc, motivo=_MOTIVO_OK),
        cert_repo=cert_repo, analise_repo=analise_repo,
    )
    assert list(v2.snapshot_padroes_usados_json) == []


def test_reemitir_motivo_curto():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    v1 = _emitir_v1(cert_repo, analise_repo, cal, cmc)
    with pytest.raises(MotivoReemissaoInsuficienteError):
        reemitir_certificado(
            _reemitir_input(v1, cal, perfil="A", cmc=cmc, motivo="curto"),
            cert_repo=cert_repo, analise_repo=analise_repo,
        )


def test_reemitir_cas_falha_conflito_409():
    cert_repo, analise_repo = FakeCertRepo(), FakeAnaliseRepo()
    cal = _calibracao()
    cmc = FakeCmc({Decimal("100"): Decimal("0.5")})
    v1 = _emitir_v1(cert_repo, analise_repo, cal, cmc)
    cert_repo.marcar_ok = False  # corrida — outro processo já substituiu
    with pytest.raises(ReemissaoConflitanteError):
        reemitir_certificado(
            _reemitir_input(v1, cal, perfil="A", cmc=cmc, motivo=_MOTIVO_OK),
            cert_repo=cert_repo, analise_repo=analise_repo,
        )
