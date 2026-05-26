"""Testes use case registrar_leitura (P4 Fase 5 Batch C — T-CAL-085).

INSERT em Leitura com idempotencia sync mobile (ADR-0027 + INV-CAL-CONC-001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConfigurarCalibracaoInput,
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
from src.application.metrologia.calibracao.registrar_leitura import (
    ConflitoLeituraExistente,
    EstadoInvalidoParaRegistrarLeitura,
    RegistrarLeituraInput,
    executar,
)
from src.domain.metrologia.calibracao.entities import LeituraSnapshot, OrigemLeitura
from src.domain.metrologia.calibracao.enums import (
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository

# =====================================================================
# FakeLeituraRepository
# =====================================================================


@dataclass
class FakeLeituraRepository:
    """In-memory repo de leituras pra testes."""

    leituras: dict[UUID, LeituraSnapshot] = field(default_factory=dict)
    # Indices auxiliares para UNIQUE composta + client_event
    _por_chave: dict[tuple[UUID, UUID, Decimal, int], UUID] = field(default_factory=dict)
    _por_client_event: dict[tuple[UUID, UUID, UUID], UUID] = field(default_factory=dict)

    def salvar_nova(self, snapshot: LeituraSnapshot) -> None:
        chave = (
            snapshot.tenant_id,
            snapshot.calibracao_id,
            snapshot.ponto_calibracao,
            snapshot.numero_repeticao,
        )
        if chave in self._por_chave:
            existente = self.leituras[self._por_chave[chave]]
            raise ConflitoLeituraExistente(existente)
        self.leituras[snapshot.id] = snapshot
        self._por_chave[chave] = snapshot.id
        if snapshot.client_event_id is not None:
            evt_chave = (snapshot.tenant_id, snapshot.calibracao_id, snapshot.client_event_id)
            self._por_client_event[evt_chave] = snapshot.id

    def obter_por_id(self, leitura_id: UUID) -> LeituraSnapshot | None:
        return self.leituras.get(leitura_id)

    def obter_por_client_event(
        self, tenant_id: UUID, calibracao_id: UUID, client_event_id: UUID
    ) -> LeituraSnapshot | None:
        evt_chave = (tenant_id, calibracao_id, client_event_id)
        leitura_id = self._por_client_event.get(evt_chave)
        if leitura_id is None:
            return None
        return self.leituras[leitura_id]


# =====================================================================
# Helpers
# =====================================================================


def _calibracao_em_execucao(repo: FakeCalibracaoRepository) -> UUID:
    """Cria + configura + inicia calibracao; retorna seu id (em EM_EXECUCAO)."""
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
    iniciar_executar(
        IniciarLeiturasInput(calibracao_id=criada.snapshot.id, revision_esperada=1),
        repo,
    )
    return criada.snapshot.id


def _input_leitura(calibracao_id: UUID, **overrides: object) -> RegistrarLeituraInput:
    defaults: dict[str, object] = {
        "calibracao_id": calibracao_id,
        "ponto_calibracao": Decimal("10.000"),
        "numero_repeticao": 1,
        "valor_lido": Decimal("10.001"),
        "unidade": "kg",
        "origem": OrigemLeitura.MANUAL,
        "timestamp": datetime(2026, 5, 25, 16, 0, tzinfo=UTC),
        "executor_id_hash": "v01$" + "e" * 16,
        "correlation_id": uuid4(),
        "client_event_id": None,
    }
    defaults.update(overrides)
    return RegistrarLeituraInput(**defaults)  # type: ignore[arg-type]


# =====================================================================
# Happy path
# =====================================================================


class TestHappyPath:
    def test_registra_leitura_em_em_execucao(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_leitura(cal_id), cal_repo, leit_repo)
        assert out.idempotente is False
        assert out.snapshot.calibracao_id == cal_id
        assert out.snapshot.ponto_calibracao == Decimal("10.000")
        assert out.snapshot.numero_repeticao == 1
        assert out.snapshot.valor_lido == Decimal("10.001")

    def test_idempotencia_client_event(self) -> None:
        """Mesmo client_event_id -> retorna leitura existente (idempotente)."""
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        evt_id = uuid4()
        primeiro = executar(
            _input_leitura(cal_id, client_event_id=evt_id),
            cal_repo,
            leit_repo,
        )
        # Segunda chamada com mesmo client_event — idempotente
        segundo = executar(
            _input_leitura(cal_id, client_event_id=evt_id, valor_lido=Decimal("99")),
            cal_repo,
            leit_repo,
        )
        assert segundo.idempotente is True
        # Retorna a primeira leitura (NAO a segunda com valor=99)
        assert segundo.snapshot.id == primeiro.snapshot.id
        assert segundo.snapshot.valor_lido == Decimal("10.001")

    def test_multiplas_repeticoes_mesmo_ponto(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        for rep in (1, 2, 3, 4, 5):
            out = executar(
                _input_leitura(cal_id, numero_repeticao=rep),
                cal_repo,
                leit_repo,
            )
            assert out.snapshot.numero_repeticao == rep
        assert len(leit_repo.leituras) == 5


# =====================================================================
# Validacoes input
# =====================================================================


class TestValidacoesInput:
    def test_rejeita_ponto_float(self) -> None:
        with pytest.raises(TypeError, match="ponto_calibracao deve ser Decimal"):
            _input_leitura(uuid4(), ponto_calibracao=10.0)

    def test_rejeita_valor_float(self) -> None:
        with pytest.raises(TypeError, match="valor_lido deve ser Decimal"):
            _input_leitura(uuid4(), valor_lido=10.0)

    def test_rejeita_repeticao_zero(self) -> None:
        with pytest.raises(ValueError, match="numero_repeticao >= 1"):
            _input_leitura(uuid4(), numero_repeticao=0)

    def test_rejeita_timestamp_sem_tz(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            _input_leitura(uuid4(), timestamp=datetime(2026, 5, 25, 16, 0))

    def test_rejeita_executor_hash_vazio(self) -> None:
        with pytest.raises(ValueError, match="executor_id_hash"):
            _input_leitura(uuid4(), executor_id_hash="")

    def test_rejeita_unidade_vazia(self) -> None:
        with pytest.raises(ValueError, match="unidade"):
            _input_leitura(uuid4(), unidade="")


# =====================================================================
# Validacoes estado + conflito
# =====================================================================


class TestEstadoEConflitos:
    def test_calibracao_nao_encontrada(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        with pytest.raises(CalibracaoNaoEncontrada):
            executar(_input_leitura(uuid4()), cal_repo, leit_repo)

    def test_estado_recepcionada_recusa(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
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
            cal_repo,
        )
        with pytest.raises(EstadoInvalidoParaRegistrarLeitura, match="EM_EXECUCAO"):
            executar(_input_leitura(criada.snapshot.id), cal_repo, leit_repo)

    def test_unique_composta_violada_levanta(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        executar(_input_leitura(cal_id, numero_repeticao=1), cal_repo, leit_repo)
        # Mesmo ponto+repeticao -> ConflitoLeituraExistente
        with pytest.raises(ConflitoLeituraExistente):
            executar(_input_leitura(cal_id, numero_repeticao=1), cal_repo, leit_repo)


def test_repository_protocol_compativel() -> None:
    """FakeLeituraRepository implementa o Protocol LeituraRepository."""
    from src.domain.metrologia.calibracao.repository import LeituraRepository

    repo = FakeLeituraRepository()
    assert isinstance(repo, LeituraRepository)
