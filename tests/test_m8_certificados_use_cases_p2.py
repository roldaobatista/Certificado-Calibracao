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
    ReconciliacaoPendenteDecisaoRTError,
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
        return True


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


def _emitir_input(cal, *, pontos, orcs, perfil, cmc, versao=1):
    return EmitirCertificadoInput(
        tenant_id=_TENANT, calibracao=cal, pontos_medidos=pontos, orcamentos_por_ponto=orcs,
        perfil=perfil, numero_interno=1, numero_certificado="BALANCAS-2026-000001",
        snapshot_padroes_usados_json=[{"padrao_id": "p1"}], data_emissao=_DATA, emitido_em=_NOW,
        correlation_id=uuid4(), cmc_para=cmc, versao=versao,
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
