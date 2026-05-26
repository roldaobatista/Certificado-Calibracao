"""Testes subcontratacao cl. 6.6 — US-CAL-017 (Batch I — T-CAL-093/094).

Cobre transicoes CONFIGURADA -> AGUARDANDO_SUBCONTRATADO ->
RECEBIDA_DO_SUBCONTRATADO + ACs AC-CAL-017-1/3/7/8 + invariantes
INV-CAL-SUBC-001/003 + INV-CAL-FRAUDE-RECEB-001.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConfigurarCalibracaoInput,
    ConflitoVersaoCalibracao,
)
from src.application.metrologia.calibracao.configurar_calibracao import (
    executar as configurar_executar,
)
from src.application.metrologia.calibracao.criar_calibracao import (
    CriarCalibracaoInput,
)
from src.application.metrologia.calibracao.criar_calibracao import (
    executar as criar_executar,
)
from src.application.metrologia.calibracao.subcontratacao import (
    AssinaturaTouchAltoRiscoSemDeclaracao,
    EstadoInvalidoParaRegistrarRecebimento,
    EstadoInvalidoParaSubcontratar,
    RegistrarRecebimentoSubcontratadoInput,
    SubcontratarCalibracaoInput,
    TransferenciaInternacionalSemBaseLGPD,
    registrar_recebimento_subcontratado,
    subcontratar_calibracao,
)
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository


def _cert_externo_padrao() -> dict[str, object]:
    return {
        "numero_cert_externo": "CERT-LAB-EXT-2026-0042",
        "data_servico": "2026-05-26",
        "grandeza": "massa",
        "faixa_min": "0",
        "faixa_max": "50000",
        "escopo_subcontratado": "RBC nº 999",
        "rt_subcontratado": "Joao Silva (CREA-SP 12345)",
    }


def _ate_configurada(repo: FakeCalibracaoRepository) -> UUID:
    """Sobe calibracao ate CONFIGURADA."""
    criada = criar_executar(
        CriarCalibracaoInput(
            tenant_id=uuid4(),
            origem_recepcao=OrigemRecepcao.AVULSA,
            atividade_os_id=None,
            instrumento_id=uuid4(),
            snapshot_equipamento_json={"nome": "Balanca"},
            cliente_id=uuid4(),
            cliente_referencia_hash="v01$aGVsbG8=",
            cliente_key_id="cliente-key-v1",
            tipo_acreditacao=TipoAcreditacao.NAO_RBC,
            recepcionada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
            correlation_id=uuid4(),
        ),
        repo,
    )
    configurar_executar(
        ConfigurarCalibracaoInput(
            calibracao_id=criada.snapshot.id,
            revision_esperada=0,
            procedimento_id=uuid4(),
            procedimento_versao_snapshot={
                "codigo": "PRO-MASSA",
                "versao": "1.0",
                "hash_anexo": "v01$abc=",
            },
            regra_decisao=RegraDecisao.ACEITACAO_SIMPLES,
            regra_decisao_acordada_em=datetime(2026, 5, 26, 15, 0, tzinfo=UTC),
            regra_decisao_acordada_documento_id=uuid4(),
            escopo_id=None,
            analise_critica_pedido_id=None,
            analise_critica_pedido_inline_hash="v01$" + "a" * 16,
            capacidade_tecnica_confirmada_por_user_id=uuid4(),
        ),
        repo,
    )
    return criada.snapshot.id


def _subc_input_padrao(
    cal_id: UUID, revision: int = 1, **overrides: object
) -> SubcontratarCalibracaoInput:
    defaults: dict[str, object] = {
        "calibracao_id": cal_id,
        "revision_esperada": revision,
        "subcontratado_id": uuid4(),
        "aceite_subcontratacao_id": uuid4(),
        "motivo_canonicalizado": (
            "Grandeza fora do escopo CMC do tenant principal apos analise."
        ),
        "motivo_hash": "v01$motivo123",
        "eh_pais_estrangeiro": False,
        "dpa_clausulas_internacionais_id": None,
        "assinatura_modo": "A3",
        "declaracao_aceite_touch_alto_risco_id": None,
    }
    defaults.update(overrides)
    return SubcontratarCalibracaoInput(**defaults)  # type: ignore[arg-type]


# ======================================================================
# subcontratar_calibracao
# ======================================================================


class TestSubcontratar:
    def test_happy_a3_brasileiro(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _ate_configurada(repo)
        subcontratado_id = uuid4()
        aceite_id = uuid4()
        out = subcontratar_calibracao(
            _subc_input_padrao(
                cal_id,
                subcontratado_id=subcontratado_id,
                aceite_subcontratacao_id=aceite_id,
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.AGUARDANDO_SUBCONTRATADO
        assert out.snapshot.subcontratado_id == subcontratado_id
        assert out.snapshot.aceite_subcontratacao_id == aceite_id
        assert out.snapshot.revision == 2

    def test_estrangeiro_com_dpa_aceita(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _ate_configurada(repo)
        out = subcontratar_calibracao(
            _subc_input_padrao(
                cal_id,
                eh_pais_estrangeiro=True,
                dpa_clausulas_internacionais_id=uuid4(),
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.AGUARDANDO_SUBCONTRATADO

    def test_estrangeiro_sem_dpa_bloqueia_lgpd_art33(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _ate_configurada(repo)
        with pytest.raises(TransferenciaInternacionalSemBaseLGPD):
            subcontratar_calibracao(
                _subc_input_padrao(
                    cal_id,
                    eh_pais_estrangeiro=True,
                    dpa_clausulas_internacionais_id=None,
                ),
                repo,
            )

    def test_touch_com_declaracao_aceita(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _ate_configurada(repo)
        out = subcontratar_calibracao(
            _subc_input_padrao(
                cal_id,
                assinatura_modo="TOUCH",
                declaracao_aceite_touch_alto_risco_id=uuid4(),
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.AGUARDANDO_SUBCONTRATADO

    def test_touch_sem_declaracao_recusa_lei_14063(self) -> None:
        with pytest.raises(ValueError, match="AC-CAL-017-7"):
            _subc_input_padrao(
                cal_id=uuid4(),
                assinatura_modo="TOUCH",
                declaracao_aceite_touch_alto_risco_id=None,
            )

    def test_assinatura_modo_invalido_recusa(self) -> None:
        with pytest.raises(ValueError, match="assinatura_modo"):
            _subc_input_padrao(cal_id=uuid4(), assinatura_modo="QUALQUER_COISA")

    def test_motivo_curto_recusa(self) -> None:
        with pytest.raises(ValueError, match="motivo_canonicalizado"):
            _subc_input_padrao(cal_id=uuid4(), motivo_canonicalizado="curto")

    def test_motivo_hash_vazio_recusa(self) -> None:
        with pytest.raises(ValueError, match="motivo_hash"):
            _subc_input_padrao(cal_id=uuid4(), motivo_hash="")

    def test_calibracao_nao_encontrada(self) -> None:
        repo = FakeCalibracaoRepository()
        with pytest.raises(CalibracaoNaoEncontrada):
            subcontratar_calibracao(_subc_input_padrao(uuid4(), revision=0), repo)

    def test_estado_recepcionada_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        criada = criar_executar(
            CriarCalibracaoInput(
                tenant_id=uuid4(),
                origem_recepcao=OrigemRecepcao.AVULSA,
                atividade_os_id=None,
                instrumento_id=uuid4(),
                snapshot_equipamento_json={"nome": "x"},
                cliente_id=uuid4(),
                cliente_referencia_hash="v01$aGVsbG8=",
                cliente_key_id="k",
                tipo_acreditacao=TipoAcreditacao.NAO_RBC,
                recepcionada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
                correlation_id=uuid4(),
            ),
            repo,
        )
        with pytest.raises(EstadoInvalidoParaSubcontratar, match="CONFIGURADA"):
            subcontratar_calibracao(
                _subc_input_padrao(criada.snapshot.id, revision=0), repo
            )

    def test_conflito_versao(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _ate_configurada(repo)
        with pytest.raises(ConflitoVersaoCalibracao):
            subcontratar_calibracao(_subc_input_padrao(cal_id, revision=99), repo)


# ======================================================================
# registrar_recebimento_subcontratado
# ======================================================================


class TestRegistrarRecebimento:
    def _ate_aguardando(self, repo: FakeCalibracaoRepository) -> UUID:
        cal_id = _ate_configurada(repo)
        subcontratar_calibracao(_subc_input_padrao(cal_id), repo)
        return cal_id

    def test_happy(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = self._ate_aguardando(repo)
        recebedor = uuid4()
        out = registrar_recebimento_subcontratado(
            RegistrarRecebimentoSubcontratadoInput(
                calibracao_id=cal_id,
                revision_esperada=2,
                recebedor_user_id=recebedor,
                certificado_subcontratado_snapshot_json=_cert_externo_padrao(),
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.RECEBIDA_DO_SUBCONTRATADO
        assert out.snapshot.recebedor_user_id == recebedor
        assert out.snapshot.certificado_subcontratado_snapshot_json is not None
        assert (
            out.snapshot.certificado_subcontratado_snapshot_json["numero_cert_externo"]
            == "CERT-LAB-EXT-2026-0042"
        )

    def test_certificado_sem_chaves_obrigatorias_recusa(self) -> None:
        with pytest.raises(ValueError, match="AC-CAL-017-3"):
            RegistrarRecebimentoSubcontratadoInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                recebedor_user_id=uuid4(),
                certificado_subcontratado_snapshot_json={
                    "numero_cert_externo": "X"  # falta resto
                },
            )

    def test_certificado_vazio_recusa(self) -> None:
        with pytest.raises(ValueError, match="certificado_subcontratado_snapshot_json"):
            RegistrarRecebimentoSubcontratadoInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                recebedor_user_id=uuid4(),
                certificado_subcontratado_snapshot_json={},
            )

    def test_estado_configurada_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _ate_configurada(repo)  # nao subcontratou
        with pytest.raises(
            EstadoInvalidoParaRegistrarRecebimento, match="AGUARDANDO_SUBCONTRATADO"
        ):
            registrar_recebimento_subcontratado(
                RegistrarRecebimentoSubcontratadoInput(
                    calibracao_id=cal_id,
                    revision_esperada=1,
                    recebedor_user_id=uuid4(),
                    certificado_subcontratado_snapshot_json=_cert_externo_padrao(),
                ),
                repo,
            )

    def test_calibracao_nao_encontrada(self) -> None:
        repo = FakeCalibracaoRepository()
        with pytest.raises(CalibracaoNaoEncontrada):
            registrar_recebimento_subcontratado(
                RegistrarRecebimentoSubcontratadoInput(
                    calibracao_id=uuid4(),
                    revision_esperada=0,
                    recebedor_user_id=uuid4(),
                    certificado_subcontratado_snapshot_json=_cert_externo_padrao(),
                ),
                repo,
            )

    def test_conflito_versao(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = self._ate_aguardando(repo)
        with pytest.raises(ConflitoVersaoCalibracao):
            registrar_recebimento_subcontratado(
                RegistrarRecebimentoSubcontratadoInput(
                    calibracao_id=cal_id,
                    revision_esperada=99,
                    recebedor_user_id=uuid4(),
                    certificado_subcontratado_snapshot_json=_cert_externo_padrao(),
                ),
                repo,
            )


# ======================================================================
# Fluxo completo subcontratacao
# ======================================================================


def test_fluxo_completo_configurada_ate_recebida() -> None:
    """Smoke E2E: CONFIGURADA -> AGUARDANDO_SUBCONTRATADO -> RECEBIDA_DO_SUBCONTRATADO."""
    repo = FakeCalibracaoRepository()
    cal_id = _ate_configurada(repo)
    subcontratado_id = uuid4()
    aceite_id = uuid4()

    # Subcontrata
    out1 = subcontratar_calibracao(
        _subc_input_padrao(
            cal_id,
            subcontratado_id=subcontratado_id,
            aceite_subcontratacao_id=aceite_id,
        ),
        repo,
    )
    assert out1.snapshot.status == EstadoCalibracao.AGUARDANDO_SUBCONTRATADO

    # Recebe cert externo
    recebedor = uuid4()
    out2 = registrar_recebimento_subcontratado(
        RegistrarRecebimentoSubcontratadoInput(
            calibracao_id=cal_id,
            revision_esperada=2,
            recebedor_user_id=recebedor,
            certificado_subcontratado_snapshot_json=_cert_externo_padrao(),
        ),
        repo,
    )
    assert out2.snapshot.status == EstadoCalibracao.RECEBIDA_DO_SUBCONTRATADO
    assert out2.snapshot.subcontratado_id == subcontratado_id
    assert out2.snapshot.aceite_subcontratacao_id == aceite_id
    assert out2.snapshot.recebedor_user_id == recebedor
    assert out2.snapshot.revision == 3


def test_assinatura_touch_excecao_levantada_no_use_case_se_burlar_post_init() -> None:
    """Defesa em profundidade: __post_init__ ja bloqueia TOUCH sem declaracao,
    mas o use case tambem tem guard caso seja burlado via object.__setattr__."""
    repo = FakeCalibracaoRepository()
    cal_id = _ate_configurada(repo)
    inp = _subc_input_padrao(
        cal_id,
        assinatura_modo="TOUCH",
        declaracao_aceite_touch_alto_risco_id=uuid4(),
    )
    # Burla via object.__setattr__ (frozen dataclass)
    object.__setattr__(inp, "declaracao_aceite_touch_alto_risco_id", None)
    with pytest.raises(AssinaturaTouchAltoRiscoSemDeclaracao):
        subcontratar_calibracao(inp, repo)
