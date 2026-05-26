"""Testes use case `avaliar_conformidade` — US-CAL-006 (Batch G — T-CAL-086).

Smoke + happy + casos de zona + estados invalidos + INV-CAL-DEC-004
(PFA cravada quando BANDA_GUARDA_30, PRA cravada quando RISCO_COMPARTILHADO).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.avaliar_conformidade import (
    AvaliarConformidadeInput,
    CalibracaoEstadoNaoPermiteAvaliar,
)
from src.application.metrologia.calibracao.avaliar_conformidade import (
    executar as avaliar_executar,
)
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
from src.application.metrologia.calibracao.iniciar_leituras import (
    IniciarLeiturasInput,
)
from src.application.metrologia.calibracao.iniciar_leituras import (
    executar as iniciar_executar,
)
from src.domain.metrologia.calibracao.enums import (
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository


def _sobe_ate_em_execucao(
    repo: FakeCalibracaoRepository,
    regra: RegraDecisao = RegraDecisao.ACEITACAO_SIMPLES,
) -> UUID:
    """Cria + configura + inicia calibracao com a regra escolhida."""
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
                "codigo": "PRO",
                "versao": "1.0",
                "hash_anexo": "v01$abc=",
            },
            regra_decisao=regra,
            regra_decisao_acordada_em=datetime(2026, 5, 26, 15, 0, tzinfo=UTC),
            regra_decisao_acordada_documento_id=uuid4(),
            escopo_id=None,
            analise_critica_pedido_id=None,
            analise_critica_pedido_inline_hash="v01$" + "a" * 16,
            capacidade_tecnica_confirmada_por_user_id=uuid4(),
        ),
        repo,
    )
    iniciar_executar(
        IniciarLeiturasInput(
            calibracao_id=criada.snapshot.id,
            revision_esperada=1,
            executor_id=uuid4(),
        ),
        repo,
    )
    return criada.snapshot.id


def _input(
    cal_id: UUID,
    revision: int,
    valor: str = "100",
    U: str = "5",
    lsl: str | None = "90",
    usl: str | None = "110",
) -> AvaliarConformidadeInput:
    return AvaliarConformidadeInput(
        calibracao_id=cal_id,
        revision_esperada=revision,
        valor_medido=Decimal(valor),
        U_expandida=Decimal(U),
        k=Decimal("2"),
        lsl=Decimal(lsl) if lsl is not None else None,
        usl=Decimal(usl) if usl is not None else None,
    )


class TestHappyPath:
    def test_aceitacao_simples_pass(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _sobe_ate_em_execucao(repo)
        out = avaliar_executar(_input(cal_id, 2), repo)
        assert out.zona == ZonaILACG8.PASS
        assert out.snapshot.decisao == "CONFORME"
        # PFA/PRA opcionais em ACEITACAO_SIMPLES
        assert out.pfa is None
        assert out.pra is None
        assert out.snapshot.revision == 3

    def test_aceitacao_simples_fail(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _sobe_ate_em_execucao(repo)
        out = avaliar_executar(_input(cal_id, 2, valor="120", U="2"), repo)
        assert out.zona == ZonaILACG8.FAIL
        assert out.snapshot.decisao == "NAO_CONFORME"

    def test_banda_guarda_pass_calcula_pfa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _sobe_ate_em_execucao(repo, regra=RegraDecisao.BANDA_GUARDA_30)
        out = avaliar_executar(_input(cal_id, 2, valor="100", U="2"), repo)
        assert out.zona == ZonaILACG8.PASS
        # INV-CAL-DEC-004: BANDA_GUARDA_30 cravou PFA
        assert out.pfa is not None
        assert out.pra is None
        assert out.snapshot.pfa_calculada == out.pfa

    def test_risco_compartilhado_calcula_pra(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _sobe_ate_em_execucao(repo, regra=RegraDecisao.RISCO_COMPARTILHADO)
        out = avaliar_executar(_input(cal_id, 2, valor="100", U="2"), repo)
        assert out.zona == ZonaILACG8.PASS
        # INV-CAL-DEC-004: RISCO_COMPARTILHADO cravou PRA
        assert out.pra is not None
        assert out.pfa is None
        assert out.snapshot.pra_calculada == out.pra

    def test_sem_limites_classifica_NA(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _sobe_ate_em_execucao(repo)
        out = avaliar_executar(
            _input(cal_id, 2, valor="100", U="5", lsl=None, usl=None), repo
        )
        assert out.zona == ZonaILACG8.NA
        assert out.snapshot.decisao == "NA"
        # NA nao calcula PFA/PRA (mesmo que regra fosse BANDA_GUARDA — nao se aplica)
        assert out.pfa is None
        assert out.pra is None


class TestEstadosInvalidos:
    def test_recepcionada_recusa(self) -> None:
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
        with pytest.raises(CalibracaoEstadoNaoPermiteAvaliar):
            avaliar_executar(_input(criada.snapshot.id, 0), repo)

    def test_calibracao_nao_encontrada(self) -> None:
        repo = FakeCalibracaoRepository()
        with pytest.raises(CalibracaoNaoEncontrada):
            avaliar_executar(_input(uuid4(), 0), repo)

    def test_conflito_versao(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _sobe_ate_em_execucao(repo)
        with pytest.raises(ConflitoVersaoCalibracao):
            avaliar_executar(_input(cal_id, 99), repo)


class TestReexecucao:
    def test_multiplas_chamadas_atualizam_zona(self) -> None:
        """Re-avaliacao apos corrigir leitura: cada chamada incrementa revision."""
        repo = FakeCalibracaoRepository()
        cal_id = _sobe_ate_em_execucao(repo)
        # 1a: PASS (valor=100, U=5)
        out1 = avaliar_executar(_input(cal_id, 2, valor="100", U="5"), repo)
        assert out1.zona == ZonaILACG8.PASS
        # 2a: FAIL (valor=120, U=5) — mesma calibracao re-avaliada
        out2 = avaliar_executar(_input(cal_id, 3, valor="120", U="5"), repo)
        assert out2.zona == ZonaILACG8.FAIL
        assert out2.snapshot.revision == 4


class TestValidacoesInput:
    def test_valor_medido_nao_decimal_recusa(self) -> None:
        with pytest.raises(TypeError, match="valor_medido"):
            AvaliarConformidadeInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                valor_medido=100.0,  # type: ignore[arg-type]
                U_expandida=Decimal("5"),
                k=Decimal("2"),
                lsl=Decimal("90"),
                usl=Decimal("110"),
            )

    def test_U_negativa_recusa(self) -> None:
        with pytest.raises(ValueError, match="U_expandida"):
            AvaliarConformidadeInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                valor_medido=Decimal("100"),
                U_expandida=Decimal("-1"),
                k=Decimal("2"),
                lsl=Decimal("90"),
                usl=Decimal("110"),
            )

    def test_k_zero_recusa(self) -> None:
        with pytest.raises(ValueError, match="k"):
            AvaliarConformidadeInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                valor_medido=Decimal("100"),
                U_expandida=Decimal("5"),
                k=Decimal("0"),
                lsl=Decimal("90"),
                usl=Decimal("110"),
            )
