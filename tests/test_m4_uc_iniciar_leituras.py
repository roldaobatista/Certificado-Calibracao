"""Testes use case iniciar_leituras (P4 Fase 5 Batch C — T-CAL-084).

US-CAL-004 — transicao CONFIGURADA -> EM_EXECUCAO com CAS.
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
from src.application.metrologia.calibracao.iniciar_leituras import (
    EstadoInvalidoParaIniciarLeituras,
    IniciarLeiturasInput,
    executar,
)
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository


def _calibracao_configurada(repo: FakeCalibracaoRepository) -> UUID:
    """Cria + configura calibracao; retorna seu id (em CONFIGURADA)."""
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
            recepcionada_em=datetime(2026, 5, 25, 14, 0, tzinfo=UTC),
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
                "codigo": "PRO-CAL-MASSA",
                "versao": "1.0.0",
                "hash_anexo": "v01$abc=",
            },
            regra_decisao=RegraDecisao.BANDA_GUARDA_30,
            regra_decisao_acordada_em=datetime(2026, 5, 25, 15, 0, tzinfo=UTC),
            regra_decisao_acordada_documento_id=uuid4(),
            escopo_id=None,
            analise_critica_pedido_id=None,
            analise_critica_pedido_inline_hash="v01$" + "a" * 16,
            capacidade_tecnica_confirmada_por_user_id=uuid4(),
        ),
        repo,
    )
    return criada.snapshot.id


def test_happy_configurada_para_em_execucao() -> None:
    repo = FakeCalibracaoRepository()
    cal_id = _calibracao_configurada(repo)
    out = executar(IniciarLeiturasInput(calibracao_id=cal_id, revision_esperada=1, executor_id=uuid4()), repo)
    assert out.snapshot.status == EstadoCalibracao.EM_EXECUCAO
    assert out.snapshot.revision == 2  # configurar incrementou pra 1; iniciar pra 2


def test_calibracao_nao_encontrada() -> None:
    repo = FakeCalibracaoRepository()
    with pytest.raises(CalibracaoNaoEncontrada):
        executar(
            IniciarLeiturasInput(
                calibracao_id=uuid4(), revision_esperada=0, executor_id=uuid4()
            ),
            repo,
        )


def test_estado_recepcionada_recusa() -> None:
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
            recepcionada_em=datetime(2026, 5, 25, 14, 0, tzinfo=UTC),
            correlation_id=uuid4(),
        ),
        repo,
    )
    # Esta em RECEPCIONADA, nao CONFIGURADA — iniciar_leituras deve recusar
    with pytest.raises(EstadoInvalidoParaIniciarLeituras, match="CONFIGURADA"):
        executar(
            IniciarLeiturasInput(
                calibracao_id=criada.snapshot.id,
                revision_esperada=0,
                executor_id=uuid4(),
            ),
            repo,
        )


def test_conflito_versao_revision_errada() -> None:
    repo = FakeCalibracaoRepository()
    cal_id = _calibracao_configurada(repo)
    # Revision real eh 1 (apos configurar); passar 99 perde CAS
    with pytest.raises(ConflitoVersaoCalibracao):
        executar(
            IniciarLeiturasInput(
                calibracao_id=cal_id, revision_esperada=99, executor_id=uuid4()
            ),
            repo,
        )


def test_segunda_chamada_em_em_execucao_recusa() -> None:
    """Apos iniciar uma vez, segunda chamada falha em EstadoInvalido (ja EM_EXECUCAO)."""
    repo = FakeCalibracaoRepository()
    cal_id = _calibracao_configurada(repo)
    executar(IniciarLeiturasInput(calibracao_id=cal_id, revision_esperada=1, executor_id=uuid4()), repo)
    with pytest.raises(EstadoInvalidoParaIniciarLeituras):
        executar(
            IniciarLeiturasInput(
                calibracao_id=cal_id, revision_esperada=2, executor_id=uuid4()
            ),
            repo,
        )
