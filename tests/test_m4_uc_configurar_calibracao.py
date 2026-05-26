"""Testes use case `configurar_calibracao` (P4 Fase 5 Batch B — T-CAL-082).

US-CAL-002 — transicao RECEPCIONADA -> CONFIGURADA com CAS.

Casos cobertos:
  - Happy AVULSA (analise_critica_pedido_inline_hash + capacidade_tecnica).
  - Happy ATIVIDADE_OS (analise_critica_pedido_id FK).
  - Rejeicao status != RECEPCIONADA (INV-CAL-WORM-001).
  - Rejeicao calibracao nao encontrada (RLS filtrou).
  - Rejeicao ADR-0023: avulsa sem inline_hash / avulsa sem capacidade /
    avulsa com FK / atividade_os sem FK / atividade_os com inline_hash.
  - Rejeicao RBC sem escopo_id (INV-CAL-CMC-001).
  - Rejeicao procedimento_versao_snapshot sem chaves canonicas.
  - Rejeicao regra_decisao_acordada_em sem tz (INV-VIG-004).
  - CAS perdido -> ConflitoVersaoCalibracao + snapshot atualizado.
  - Snapshot pos-execucao: status=CONFIGURADA, revision=+1, fields cravados.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConfigurarCalibracaoInput,
    ConflitoVersaoCalibracao,
    EstadoInvalidoParaConfigurar,
    executar,
)
from src.application.metrologia.calibracao.criar_calibracao import (
    CriarCalibracaoInput,
)
from src.application.metrologia.calibracao.criar_calibracao import (
    executar as criar_executar,
)
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository

# =====================================================================
# Builders
# =====================================================================


def _criar_calibracao_avulsa(
    repo: FakeCalibracaoRepository,
    tipo_acreditacao: TipoAcreditacao = TipoAcreditacao.NAO_RBC,
) -> UUID:
    """Cria calibracao AVULSA em RECEPCIONADA e retorna seu id."""
    out = criar_executar(
        CriarCalibracaoInput(
            tenant_id=uuid4(),
            origem_recepcao=OrigemRecepcao.AVULSA,
            atividade_os_id=None,
            instrumento_id=uuid4(),
            snapshot_equipamento_json={"nome": "Balanca"},
            cliente_id=uuid4(),
            cliente_referencia_hash="v01$aGVsbG8=",
            cliente_key_id="cliente-key-v1",
            tipo_acreditacao=tipo_acreditacao,
            recepcionada_em=datetime(2026, 5, 25, 14, 0, tzinfo=UTC),
            correlation_id=uuid4(),
        ),
        repo,
    )
    return out.snapshot.id


def _criar_calibracao_os(
    repo: FakeCalibracaoRepository,
) -> UUID:
    """Cria calibracao plugada em ATIVIDADE_OS em RECEPCIONADA."""
    out = criar_executar(
        CriarCalibracaoInput(
            tenant_id=uuid4(),
            origem_recepcao=OrigemRecepcao.ATIVIDADE_OS,
            atividade_os_id=uuid4(),
            instrumento_id=uuid4(),
            snapshot_equipamento_json={"nome": "Termometro"},
            cliente_id=uuid4(),
            cliente_referencia_hash="v01$aGVsbG8=",
            cliente_key_id="cliente-key-v1",
            tipo_acreditacao=TipoAcreditacao.NAO_RBC,
            recepcionada_em=datetime(2026, 5, 25, 14, 0, tzinfo=UTC),
            correlation_id=uuid4(),
        ),
        repo,
    )
    return out.snapshot.id


def _input_avulsa(calibracao_id: UUID, revision: int = 0, **overrides: object) -> ConfigurarCalibracaoInput:
    defaults: dict[str, object] = {
        "calibracao_id": calibracao_id,
        "revision_esperada": revision,
        "procedimento_id": uuid4(),
        "procedimento_versao_snapshot": {
            "codigo": "PRO-CAL-MASSA",
            "versao": "1.0.0",
            "hash_anexo": "v01$abc=",
        },
        "regra_decisao": RegraDecisao.BANDA_GUARDA_30,
        "regra_decisao_acordada_em": datetime(2026, 5, 25, 15, 0, tzinfo=UTC),
        "regra_decisao_acordada_documento_id": uuid4(),
        "escopo_id": None,  # NAO_RBC default
        "analise_critica_pedido_id": None,
        "analise_critica_pedido_inline_hash": "v01$" + "a" * 16,
        "capacidade_tecnica_confirmada_por_user_id": uuid4(),
    }
    defaults.update(overrides)
    return ConfigurarCalibracaoInput(**defaults)  # type: ignore[arg-type]


# =====================================================================
# Happy path
# =====================================================================


class TestHappyPath:
    def test_avulsa_configura_em_configurada(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        out = executar(_input_avulsa(cal_id), repo)
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA
        assert out.snapshot.revision == 1
        assert out.snapshot.regra_decisao == RegraDecisao.BANDA_GUARDA_30
        assert out.snapshot.procedimento_id is not None
        assert out.snapshot.analise_critica_pedido_inline_hash != ""
        assert out.snapshot.capacidade_tecnica_confirmada_por_user_id is not None

    def test_atividade_os_configura_com_fk(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_os(repo)
        ac_id = uuid4()
        out = executar(
            _input_avulsa(
                cal_id,
                analise_critica_pedido_id=ac_id,
                analise_critica_pedido_inline_hash="",
                capacidade_tecnica_confirmada_por_user_id=None,
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA
        assert out.snapshot.analise_critica_pedido_id == ac_id
        assert out.snapshot.analise_critica_pedido_inline_hash == ""

    def test_rbc_com_escopo_id(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        escopo = uuid4()
        out = executar(_input_avulsa(cal_id, escopo_id=escopo), repo)
        assert out.snapshot.escopo_id == escopo

    def test_snapshot_persistido_no_repo(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        out = executar(_input_avulsa(cal_id), repo)
        # Reload do repo confere
        atualizado = repo.obter_por_id(cal_id)
        assert atualizado == out.snapshot

    def test_revision_incrementa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        antes = repo.obter_por_id(cal_id)
        assert antes is not None
        assert antes.revision == 0
        out = executar(_input_avulsa(cal_id, revision=0), repo)
        assert out.snapshot.revision == 1


# =====================================================================
# Validacao estado
# =====================================================================


class TestValidacaoEstado:
    def test_calibracao_nao_encontrada(self) -> None:
        repo = FakeCalibracaoRepository()
        with pytest.raises(CalibracaoNaoEncontrada):
            executar(_input_avulsa(uuid4()), repo)

    def test_estado_nao_recepcionada_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        # Configura uma vez -> agora esta CONFIGURADA
        executar(_input_avulsa(cal_id), repo)
        # Tentar configurar de novo deve recusar
        with pytest.raises(EstadoInvalidoParaConfigurar, match="RECEPCIONADA"):
            executar(_input_avulsa(cal_id, revision=1), repo)


# =====================================================================
# Validacao ADR-0023 (analise critica vs origem)
# =====================================================================


class TestAnaliseCriticaCoerencia:
    def test_avulsa_sem_inline_hash_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        with pytest.raises(ValueError, match="inline_hash"):
            executar(
                _input_avulsa(cal_id, analise_critica_pedido_inline_hash=""),
                repo,
            )

    def test_avulsa_sem_capacidade_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        with pytest.raises(ValueError, match="capacidade_tecnica"):
            executar(
                _input_avulsa(cal_id, capacidade_tecnica_confirmada_por_user_id=None),
                repo,
            )

    def test_avulsa_com_fk_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        with pytest.raises(ValueError, match="AVULSA proibe analise_critica_pedido_id"):
            executar(
                _input_avulsa(cal_id, analise_critica_pedido_id=uuid4()),
                repo,
            )

    def test_atividade_os_sem_fk_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_os(repo)
        with pytest.raises(ValueError, match="analise_critica_pedido_id"):
            executar(
                _input_avulsa(cal_id, analise_critica_pedido_id=None, analise_critica_pedido_inline_hash=""),
                repo,
            )

    def test_atividade_os_com_inline_hash_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_os(repo)
        with pytest.raises(ValueError, match="ATIVIDADE_OS proibe inline_hash"):
            executar(
                _input_avulsa(
                    cal_id,
                    analise_critica_pedido_id=uuid4(),
                    analise_critica_pedido_inline_hash="v01$aaaaaaaaaaaaaaaa",
                ),
                repo,
            )


# =====================================================================
# Validacao RBC + procedimento
# =====================================================================


class TestValidacoesExtras:
    def test_rbc_sem_escopo_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        with pytest.raises(ValueError, match="escopo_id NOT NULL"):
            executar(_input_avulsa(cal_id, escopo_id=None), repo)

    def test_procedimento_snapshot_sem_chaves_recusa(self) -> None:
        with pytest.raises(ValueError, match="procedimento_versao_snapshot"):
            _input_avulsa(
                uuid4(),
                procedimento_versao_snapshot={"codigo": "X"},  # falta versao + hash_anexo
            )

    def test_regra_decisao_acordada_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            _input_avulsa(
                uuid4(),
                regra_decisao_acordada_em=datetime(2026, 5, 25, 15, 0),  # sem tz
            )


# =====================================================================
# Concorrencia CAS (ADR-0065)
# =====================================================================


class TestConcorrenciaCAS:
    def test_conflito_versao_revision_errada(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        # Caller acha que revision=99 mas snapshot real eh 0
        with pytest.raises(ConflitoVersaoCalibracao) as exc:
            executar(_input_avulsa(cal_id, revision=99), repo)
        # Excecao carrega snapshot atual pra retry
        assert exc.value.snapshot_atual.revision == 0
        assert exc.value.snapshot_atual.status == EstadoCalibracao.RECEPCIONADA

    def test_revision_atualizada_mas_estado_inicial_diferente(self) -> None:
        """Cenario real concorrente: worker 1 lê snapshot revision=0 + status=RECEPCIONADA;
        worker 2 configura primeiro (-> revision=1, status=CONFIGURADA); worker 1 tenta
        configurar com revision_esperada=0 — caí em EstadoInvalidoParaConfigurar (estado
        ja avançou) ANTES do CAS — comportamento correto: estado é verificado antes."""
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo)
        executar(_input_avulsa(cal_id, revision=0), repo)
        # Worker 1 atrasado tenta configurar a calibracao ja CONFIGURADA
        with pytest.raises(EstadoInvalidoParaConfigurar):
            executar(_input_avulsa(cal_id, revision=0), repo)
