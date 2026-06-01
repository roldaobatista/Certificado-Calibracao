"""M8 Fatia 1a (T-CER-010..018) — domínio puro persistível do certificado.

Sem Django, sem PG (`--no-cov` fora do Docker): enums de ciclo de vida,
`reconciliacao_hash` determinístico, snapshots WORM (round-trip), máquina de
estados, completude de decisões RT, coerência classificação↔categoria, Protocols.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.metrologia.certificados.entities import (
    AnaliseReconciliacaoCertificado,
    CertificadoSnapshot,
    PontoReconciliadoSnapshot,
)
from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
    TipoAcreditacao,
)
from src.domain.metrologia.certificados.erros import (
    MotivoReemissaoInsuficienteError,
    ReconciliacaoPendenteDecisaoRTError,
    RessalvaNaoRbcObrigatoriaError,
    TransicaoCertificadoInvalidaError,
)
from src.domain.metrologia.certificados.reconciliacao import PontoReconciliado
from src.domain.metrologia.certificados.reconciliacao_hash import reconciliacao_hash
from src.domain.metrologia.certificados.repository import (
    AnaliseReconciliacaoRepository,
    CertificadoRepository,
)
from src.domain.metrologia.certificados.transicoes import (
    categoria_coerente,
    exigir_ressalva_nao_rbc,
    exigir_transicao,
    pode_transicionar,
    validar_completude_decisoes_rt,
    validar_motivo_reemissao,
)

_TENANT = uuid4()
_NOW = datetime(2026, 5, 31, 12, 0, tzinfo=UTC)


def _pr(ponto: str, *, classificacao=ClassificacaoPonto.RBC_OK, incluido=True, cmc="0.5", suspeita=False) -> PontoReconciliado:
    return PontoReconciliado(
        ponto_calibracao=Decimal(ponto),
        valor_reportado=Decimal(ponto),
        U_no_ponto=Decimal("0.8"),
        k_no_ponto=Decimal("2"),
        nivel_confianca_no_ponto=Decimal("0.9545"),
        grau_liberdade_efetivo_no_ponto=Decimal("60"),
        cmc_no_ponto=None if cmc is None else Decimal(cmc),
        classificacao=classificacao,
        u_igual_cmc_suspeita=suspeita,
        incluido_no_certificado=incluido,
    )


def _snap(pr: PontoReconciliado, **kw) -> PontoReconciliadoSnapshot:
    return PontoReconciliadoSnapshot.de_reconciliado(
        pr, id=uuid4(), tenant_id=_TENANT, certificado_id=uuid4(), **kw
    )


# --- Enums (T-CER-010) --------------------------------------------------------


def test_estado_certificado_properties():
    assert EstadoCertificado.EMITIDO.emitido
    assert not EstadoCertificado.RASCUNHO.emitido
    assert EstadoCertificado.SUBSTITUIDA.terminal
    assert EstadoCertificado.REVOGADO.terminal
    assert not EstadoCertificado.EMITIDO.terminal
    assert EstadoCertificado.EMITIDO.consultavel
    assert not EstadoCertificado.RASCUNHO.consultavel


def test_estado_valores_batem_com_stub_lowercase():
    # contrato trigger INV-025 lê 'emitido' literal (ADR-0078)
    assert EstadoCertificado.EMITIDO.value == "emitido"
    assert EstadoCertificado.RASCUNHO.value == "rascunho"
    assert EstadoCertificado.REVOGADO.value == "revogado"


def test_enums_serializam_como_str():
    assert TipoAcreditacao.RBC == "RBC"
    assert DecisaoReconciliacaoRT.EXCLUIR_PONTO == "EXCLUIR_PONTO"
    assert CategoriaMotivoExclusao.OUTRO == "OUTRO"


# --- reconciliacao_hash (T-CER-011) -------------------------------------------


def _hash(pontos, *, tipo="RBC", fmin="100", fmax="500"):
    return reconciliacao_hash(
        pontos=pontos,
        versao_reconciliacao="1.0.0",
        faixa_certificado_min=Decimal(fmin) if fmin is not None else None,
        faixa_certificado_max=Decimal(fmax) if fmax is not None else None,
        tipo_acreditacao=tipo,
    )


def test_reconciliacao_hash_deterministico_e_versionado():
    pts = [_snap(_pr("100")), _snap(_pr("500"))]
    h1 = _hash(pts)
    h2 = _hash(list(reversed(pts)))  # ordem de entrada não importa (ordena ASC)
    assert h1 == h2
    assert h1.startswith("v01$")


def test_reconciliacao_hash_muda_com_classificacao():
    base = _hash([_snap(_pr("100"))])
    outro = _hash([_snap(_pr("100", classificacao=ClassificacaoPonto.U_MENOR_CMC, incluido=False))])
    assert base != outro


def test_reconciliacao_hash_faixa_zero_nao_vira_none():
    # Decimal('0') é falsy — _str_ou_none deve preservar '0', não None.
    h_zero = _hash([_snap(_pr("0", cmc=None, classificacao=ClassificacaoPonto.SEM_CMC))], fmin="0", fmax="0")
    h_none = _hash([_snap(_pr("0", cmc=None, classificacao=ClassificacaoPonto.SEM_CMC))], fmin=None, fmax=None)
    assert h_zero != h_none


def test_reconciliacao_hash_aceita_ponto_reconciliado_puro():
    # Protocol estrutural: PontoReconciliado (Fatia 0) também serve.
    assert _hash([_pr("100")]).startswith("v01$")


# --- Snapshots (T-CER-012/013) ------------------------------------------------


def test_de_reconciliado_round_trip_e_override():
    pr = _pr("100", suspeita=True)
    s = _snap(pr, ressalva_nao_rbc="x", classificacao=ClassificacaoPonto.EXCLUIDO, incluido_no_certificado=False)
    assert s.ponto_calibracao == Decimal("100")
    assert s.U_no_ponto == Decimal("0.8")
    assert s.u_igual_cmc_suspeita  # preservado do PR
    assert s.classificacao is ClassificacaoPonto.EXCLUIDO  # override RT
    assert not s.incluido_no_certificado
    assert s.ressalva_nao_rbc == "x"


def test_certificado_snapshot_round_trip_todos_os_campos():
    cid = uuid4()
    snap = CertificadoSnapshot(
        id=cid,
        tenant_id=_TENANT,
        calibracao_id=uuid4(),
        equipamento_id=uuid4(),
        numero_interno=42,
        numero_certificado="BALANCAS-2026-000042",
        versao=1,
        versao_anterior_id=None,
        status=EstadoCertificado.EMITIDO,
        perfil_emissor_no_momento="A",
        faixa_certificado_min=Decimal("100"),
        faixa_certificado_max=Decimal("500"),
        tipo_acreditacao=TipoAcreditacao.RBC,
        snapshot_equipamento_json={"tag": "BAL-01"},
        snapshot_padroes_usados_json=[{"padrao_id": "p1", "calibracao_padrao_vigencia_fim": "2027-01-01"}],
        cliente_ref_hash="v01$abc",
        reconciliacao_hash="v01$def",
        emitido_em=_NOW,
        correlation_id=uuid4(),
        regra_decisao_snapshot={"modo": "simples"},
    )
    assert snap.status is EstadoCertificado.EMITIDO
    assert snap.numero_interno == 42
    assert snap.snapshot_padroes_usados_json[0]["padrao_id"] == "p1"
    assert snap.regra_decisao_snapshot["modo"] == "simples"
    with pytest.raises((AttributeError, Exception)):  # frozen
        snap.numero_interno = 99  # type: ignore[misc]


# --- AnaliseReconciliacaoCertificado + coerência (T-CER-014) ------------------


def _analise(classif, categoria, *, decisao=DecisaoReconciliacaoRT.EXCLUIR_PONTO):
    return AnaliseReconciliacaoCertificado(
        id=uuid4(),
        tenant_id=_TENANT,
        calibracao_id=uuid4(),
        ponto_calibracao=Decimal("100"),
        decisao_rt=decisao,
        categoria_motivo=categoria,
        justificativa_canonicalizada="motivo objetivo da exclusao do ponto",
        justificativa_hash="v01$abc",
        criado_em=_NOW,
        correlation_id=uuid4(),
    )


def test_coerencia_categoria_classificacao():
    # U_MENOR_CMC + EXCLUIR_PONTO aceita U_MAIOR_QUE_CMC_BUG ou OUTRO (T-CER-014)
    assert categoria_coerente(ClassificacaoPonto.U_MENOR_CMC, CategoriaMotivoExclusao.U_MAIOR_QUE_CMC_BUG)
    assert categoria_coerente(ClassificacaoPonto.U_MENOR_CMC, CategoriaMotivoExclusao.OUTRO)
    # INCOERENTE: PONTO_FORA_FAIXA_DECLARADA para um ponto que está DENTRO
    assert not categoria_coerente(ClassificacaoPonto.U_MENOR_CMC, CategoriaMotivoExclusao.PONTO_FORA_FAIXA_DECLARADA)
    assert not categoria_coerente(ClassificacaoPonto.FORA_DECLARADA, CategoriaMotivoExclusao.U_MAIOR_QUE_CMC_BUG)
    # Categorias físicas valem para qualquer classificação problemática
    assert categoria_coerente(ClassificacaoPonto.SEM_CMC, CategoriaMotivoExclusao.PADRAO_FORA_VALIDADE)
    a = _analise(ClassificacaoPonto.FORA_DECLARADA, CategoriaMotivoExclusao.PONTO_FORA_FAIXA_DECLARADA)
    assert a.categoria_motivo is CategoriaMotivoExclusao.PONTO_FORA_FAIXA_DECLARADA


# --- Máquina de estados (T-CER-015) -------------------------------------------


def test_transicoes_validas_e_invalidas():
    assert pode_transicionar(EstadoCertificado.RASCUNHO, EstadoCertificado.EMITIDO)
    assert pode_transicionar(EstadoCertificado.EMITIDO, EstadoCertificado.SUBSTITUIDA)
    assert pode_transicionar(EstadoCertificado.EMITIDO, EstadoCertificado.REVOGADO)
    assert not pode_transicionar(EstadoCertificado.RASCUNHO, EstadoCertificado.REVOGADO)
    assert not pode_transicionar(EstadoCertificado.SUBSTITUIDA, EstadoCertificado.EMITIDO)


def test_exigir_transicao_raise_em_invalida():
    exigir_transicao(EstadoCertificado.EMITIDO, EstadoCertificado.SUBSTITUIDA)  # ok
    with pytest.raises(TransicaoCertificadoInvalidaError):
        exigir_transicao(EstadoCertificado.SUBSTITUIDA, EstadoCertificado.EMITIDO)


def test_validar_motivo_reemissao():
    validar_motivo_reemissao("x" * 50)  # ok
    with pytest.raises(MotivoReemissaoInsuficienteError):
        validar_motivo_reemissao("curto demais")


# --- Completude de decisões RT (T-CER-015 / NC-03) ----------------------------


def test_perfil_a_ponto_nao_rbc_sem_decisao_bloqueia():
    with pytest.raises(ReconciliacaoPendenteDecisaoRTError):
        validar_completude_decisoes_rt(
            pontos_nao_rbc=[Decimal("100"), Decimal("500")],
            pontos_com_decisao=[Decimal("100")],
            perfil="A",
        )


def test_perfil_a_todas_decisoes_presentes_ok():
    validar_completude_decisoes_rt(
        pontos_nao_rbc=[Decimal("100")],
        pontos_com_decisao=[Decimal("100")],
        perfil="A",
    )


def test_perfil_bcd_nao_bloqueia_mesmo_sem_decisao():
    for perfil in ("B", "C", "D"):
        validar_completude_decisoes_rt(
            pontos_nao_rbc=[Decimal("100")],
            pontos_com_decisao=[],
            perfil=perfil,
        )


# --- Ressalva não-RBC obrigatória (C-03) --------------------------------------


def test_ressalva_obrigatoria_em_emitir_nao_rbc():
    exigir_ressalva_nao_rbc(DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO, "ponto não coberto pela acreditação RBC")
    with pytest.raises(RessalvaNaoRbcObrigatoriaError):
        exigir_ressalva_nao_rbc(DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO, "   ")
    # EXCLUIR_PONTO não exige ressalva
    exigir_ressalva_nao_rbc(DecisaoReconciliacaoRT.EXCLUIR_PONTO, "")


# --- Protocols runtime_checkable (T-CER-016) ----------------------------------


def test_repository_protocols_runtime_checkable():
    class _FakeCertRepo:
        def obter_por_id(self, certificado_id): ...
        def existe_chave(self, *, tenant_id, calibracao_id, versao): ...
        def proximo_numero_interno(self, *, tenant_id): ...
        def salvar_novo(self, certificado, pontos): ...
        def marcar_substituida(self, *, certificado_id, revision_anterior): ...

    class _FakeAnaliseRepo:
        def salvar_decisao(self, decisao): ...
        def listar_por_calibracao(self, *, tenant_id, calibracao_id): ...
        def existe_decisao_para_ponto(self, *, tenant_id, calibracao_id, ponto_calibracao): ...
        def obter_decisao_por_ponto(self, *, tenant_id, calibracao_id): ...

    assert isinstance(_FakeCertRepo(), CertificadoRepository)
    assert isinstance(_FakeAnaliseRepo(), AnaliseReconciliacaoRepository)
