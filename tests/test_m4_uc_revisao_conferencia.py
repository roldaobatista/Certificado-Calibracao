"""Testes Batch F (P4 Fase 5) — solicitar/aprovar/rejeitar revisao +
aprovar 2a conferencia. US-CAL-006/007/008.

Casos cobertos:
- solicitar_revisao: EM_EXECUCAO -> EM_REVISAO_1 + CAS + rejeita outros estados.
- aprovar_revisao: EM_REVISAO_1 -> AGUARDANDO_2A_CONFERENCIA + snapshot
  competencia + INV-CAL-FRAUDE-REV-001 + excecao ADR-0026.
- rejeitar_revisao: EM_REVISAO_1 -> EM_EXECUCAO + motivo >=30 chars +
  nao queima revisor_id.
- aprovar_2a_conferencia: AGUARDANDO_2A_CONFERENCIA -> APROVADA +
  INV-CAL-FRAUDE-CONF-001 + excecao ADR-0026 + excecao_2a_conf_id
  obrigatoria quando conferente colide.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
    Aprovar2aConferenciaInput,
    EstadoInvalidoParaAprovar2aConferencia,
    FraudeConferenteEhRevisorOuExecutor,
)
from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
    executar as aprovar_2a_executar,
)
from src.application.metrologia.calibracao.aprovar_revisao import (
    AprovarRevisaoInput,
    EstadoInvalidoParaAprovarRevisao,
    ExcecaoAdr0026Invalida,
    FraudeRevisorEhExecutor,
)
from src.application.metrologia.calibracao.aprovar_revisao import (
    executar as aprovar_executar,
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
from src.application.metrologia.calibracao.rejeitar_revisao import (
    EstadoInvalidoParaRejeitarRevisao,
    RejeitarRevisaoInput,
)
from src.application.metrologia.calibracao.rejeitar_revisao import (
    executar as rejeitar_executar,
)
from src.application.metrologia.calibracao.solicitar_revisao import (
    EstadoInvalidoParaSolicitarRevisao,
    SolicitarRevisaoInput,
)
from src.application.metrologia.calibracao.solicitar_revisao import (
    executar as solicitar_executar,
)
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository

# ----------------------------------------------------------------------
# Builders — sobem a calibracao ate estado desejado
# ----------------------------------------------------------------------


def _competencia_json(grandeza: str = "massa") -> dict[str, object]:
    """Snapshot mock de RTCompetencia (M2 + ADR-0022)."""
    return {
        "grandeza": grandeza,
        "faixa_min": "0",
        "faixa_max": "10000",
        "vigencia_inicio": "2025-01-01",
        "vigencia_fim": "2027-12-31",
        "rt_competencia_id": str(uuid4()),
    }


def _calibracao_em_execucao(repo: FakeCalibracaoRepository, executor_id: UUID) -> UUID:
    """Sobe calibracao ate EM_EXECUCAO com executor cravado."""
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
            regra_decisao=RegraDecisao.ACEITACAO_SIMPLES,
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
        IniciarLeiturasInput(
            calibracao_id=criada.snapshot.id,
            revision_esperada=1,
            executor_id=executor_id,
        ),
        repo,
    )
    return criada.snapshot.id


def _calibracao_em_revisao(
    repo: FakeCalibracaoRepository, executor_id: UUID
) -> UUID:
    """Sobe ate EM_REVISAO_1 (executor cravado, revisor ainda None)."""
    cal_id = _calibracao_em_execucao(repo, executor_id)
    solicitar_executar(
        SolicitarRevisaoInput(calibracao_id=cal_id, revision_esperada=2),
        repo,
    )
    return cal_id


def _calibracao_aguardando_2a(
    repo: FakeCalibracaoRepository, executor_id: UUID, revisor_id: UUID
) -> UUID:
    """Sobe ate AGUARDANDO_2A_CONFERENCIA (executor+revisor cravados)."""
    cal_id = _calibracao_em_revisao(repo, executor_id)
    aprovar_executar(
        AprovarRevisaoInput(
            calibracao_id=cal_id,
            revision_esperada=3,
            revisor_id=revisor_id,
            snapshot_competencia_revisor_json=_competencia_json(),
        ),
        repo,
    )
    return cal_id


# =====================================================================
# solicitar_revisao
# =====================================================================


class TestSolicitarRevisao:
    def test_happy_em_execucao_para_em_revisao_1(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        cal_id = _calibracao_em_execucao(repo, executor)
        out = solicitar_executar(
            SolicitarRevisaoInput(calibracao_id=cal_id, revision_esperada=2), repo
        )
        assert out.snapshot.status == EstadoCalibracao.EM_REVISAO_1
        assert out.snapshot.revision == 3  # criar=0 -> configurar=1 -> iniciar=2 -> solicitar=3
        assert out.snapshot.executor_id == executor

    def test_calibracao_nao_encontrada(self) -> None:
        repo = FakeCalibracaoRepository()
        with pytest.raises(CalibracaoNaoEncontrada):
            solicitar_executar(
                SolicitarRevisaoInput(calibracao_id=uuid4(), revision_esperada=0),
                repo,
            )

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
                recepcionada_em=datetime(2026, 5, 25, 14, 0, tzinfo=UTC),
                correlation_id=uuid4(),
            ),
            repo,
        )
        with pytest.raises(EstadoInvalidoParaSolicitarRevisao, match="EM_EXECUCAO"):
            solicitar_executar(
                SolicitarRevisaoInput(
                    calibracao_id=criada.snapshot.id, revision_esperada=0
                ),
                repo,
            )

    def test_conflito_versao(self) -> None:
        repo = FakeCalibracaoRepository()
        cal_id = _calibracao_em_execucao(repo, uuid4())
        with pytest.raises(ConflitoVersaoCalibracao):
            solicitar_executar(
                SolicitarRevisaoInput(calibracao_id=cal_id, revision_esperada=99),
                repo,
            )


# =====================================================================
# aprovar_revisao
# =====================================================================


class TestAprovarRevisao:
    def test_happy_revisor_diferente_do_executor(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        revisor = uuid4()
        cal_id = _calibracao_em_revisao(repo, executor)
        out = aprovar_executar(
            AprovarRevisaoInput(
                calibracao_id=cal_id,
                revision_esperada=3,
                revisor_id=revisor,
                snapshot_competencia_revisor_json=_competencia_json(),
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA
        assert out.snapshot.revisor_id == revisor
        assert out.snapshot.snapshot_competencia_revisor_json is not None
        assert (
            out.snapshot.snapshot_competencia_revisor_json["grandeza"] == "massa"
        )

    def test_revisor_eh_executor_sem_excecao_bloqueia(self) -> None:
        repo = FakeCalibracaoRepository()
        ator = uuid4()  # mesmo user executou e tenta revisar
        cal_id = _calibracao_em_revisao(repo, ator)
        with pytest.raises(FraudeRevisorEhExecutor):
            aprovar_executar(
                AprovarRevisaoInput(
                    calibracao_id=cal_id,
                    revision_esperada=3,
                    revisor_id=ator,
                    snapshot_competencia_revisor_json=_competencia_json(),
                ),
                repo,
            )

    def test_revisor_eh_executor_com_excecao_adr0026_aceita(self) -> None:
        repo = FakeCalibracaoRepository()
        ator = uuid4()
        cal_id = _calibracao_em_revisao(repo, ator)
        out = aprovar_executar(
            AprovarRevisaoInput(
                calibracao_id=cal_id,
                revision_esperada=3,
                revisor_id=ator,
                snapshot_competencia_revisor_json=_competencia_json(),
                excecao_motivo="GRANDEZA_RT_UNICO_TENANT",
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA

    def test_excecao_motivo_fora_whitelist_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        ator = uuid4()
        cal_id = _calibracao_em_revisao(repo, ator)
        with pytest.raises(ExcecaoAdr0026Invalida):
            aprovar_executar(
                AprovarRevisaoInput(
                    calibracao_id=cal_id,
                    revision_esperada=3,
                    revisor_id=ator,
                    snapshot_competencia_revisor_json=_competencia_json(),
                    excecao_motivo="MOTIVO_INVENTADO",
                ),
                repo,
            )

    def test_snapshot_competencia_sem_chaves_obrigatorias_recusa(self) -> None:
        with pytest.raises(ValueError, match="snapshot_competencia_revisor_json"):
            AprovarRevisaoInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                revisor_id=uuid4(),
                snapshot_competencia_revisor_json={"grandeza": "massa"},  # falta resto
            )

    def test_snapshot_competencia_vazio_recusa(self) -> None:
        with pytest.raises(ValueError, match="snapshot_competencia_revisor_json"):
            AprovarRevisaoInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                revisor_id=uuid4(),
                snapshot_competencia_revisor_json={},
            )

    def test_estado_em_execucao_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        cal_id = _calibracao_em_execucao(repo, executor)
        # nao solicitou revisao — esta em EM_EXECUCAO
        with pytest.raises(EstadoInvalidoParaAprovarRevisao, match="EM_REVISAO_1"):
            aprovar_executar(
                AprovarRevisaoInput(
                    calibracao_id=cal_id,
                    revision_esperada=2,
                    revisor_id=uuid4(),
                    snapshot_competencia_revisor_json=_competencia_json(),
                ),
                repo,
            )

    def test_calibracao_sem_executor_bloqueia(self) -> None:
        """Defensivo: se entidade chegou em EM_REVISAO_1 sem executor cravado,
        falha — antes de checar segregacao."""
        repo = FakeCalibracaoRepository()
        # Cria + configura + transita manualmente sem cravar executor.
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
        # Forca status pra EM_REVISAO_1 sem executor (mutacao direta no fake)
        from dataclasses import replace

        snap = repo.snapshots[criada.snapshot.id]
        repo.snapshots[criada.snapshot.id] = replace(
            snap, status=EstadoCalibracao.EM_REVISAO_1, executor_id=None
        )
        with pytest.raises(EstadoInvalidoParaAprovarRevisao, match="executor_id"):
            aprovar_executar(
                AprovarRevisaoInput(
                    calibracao_id=criada.snapshot.id,
                    revision_esperada=0,
                    revisor_id=uuid4(),
                    snapshot_competencia_revisor_json=_competencia_json(),
                ),
                repo,
            )


# =====================================================================
# rejeitar_revisao
# =====================================================================


class TestRejeitarRevisao:
    def test_happy_em_revisao_volta_em_execucao(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        cal_id = _calibracao_em_revisao(repo, executor)
        out = rejeitar_executar(
            RejeitarRevisaoInput(
                calibracao_id=cal_id,
                revision_esperada=3,
                motivo_rejeicao_canonicalizado=(
                    "Componente Tipo A faltou n_amostras suficiente em ponto 5kg"
                ),
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.EM_EXECUCAO
        # Rejeicao NAO queima revisor_id — continua None
        assert out.snapshot.revisor_id is None
        assert out.snapshot.snapshot_competencia_revisor_json is None
        assert out.motivo.startswith("Componente")

    def test_motivo_curto_recusa(self) -> None:
        with pytest.raises(ValueError, match="motivo_rejeicao_canonicalizado"):
            RejeitarRevisaoInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                motivo_rejeicao_canonicalizado="muito curto",
            )

    def test_motivo_exato_30_chars_aceita(self) -> None:
        inp = RejeitarRevisaoInput(
            calibracao_id=uuid4(),
            revision_esperada=0,
            motivo_rejeicao_canonicalizado="a" * 30,
        )
        assert len(inp.motivo_rejeicao_canonicalizado) == 30

    def test_estado_em_execucao_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        cal_id = _calibracao_em_execucao(repo, executor)
        with pytest.raises(EstadoInvalidoParaRejeitarRevisao, match="EM_REVISAO_1"):
            rejeitar_executar(
                RejeitarRevisaoInput(
                    calibracao_id=cal_id,
                    revision_esperada=2,
                    motivo_rejeicao_canonicalizado="motivo suficientemente longo aaaaaaaa",
                ),
                repo,
            )


# =====================================================================
# aprovar_2a_conferencia
# =====================================================================


class TestAprovar2aConferencia:
    def test_happy_conferente_independente_aprova(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        revisor = uuid4()
        conferente = uuid4()  # 3 atores distintos — happy path
        cal_id = _calibracao_aguardando_2a(repo, executor, revisor)
        out = aprovar_2a_executar(
            Aprovar2aConferenciaInput(
                calibracao_id=cal_id,
                revision_esperada=4,
                conferente_id=conferente,
                snapshot_competencia_conferente_json=_competencia_json(),
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.APROVADA
        assert out.snapshot.conferente_id == conferente
        assert out.snapshot.snapshot_competencia_conferente_json is not None
        assert out.snapshot.excecao_2a_conf_id is None

    def test_conferente_eh_revisor_sem_excecao_bloqueia(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        revisor = uuid4()
        cal_id = _calibracao_aguardando_2a(repo, executor, revisor)
        with pytest.raises(FraudeConferenteEhRevisorOuExecutor):
            aprovar_2a_executar(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal_id,
                    revision_esperada=4,
                    conferente_id=revisor,  # colide com revisor
                    snapshot_competencia_conferente_json=_competencia_json(),
                ),
                repo,
            )

    def test_conferente_eh_executor_sem_excecao_bloqueia(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        revisor = uuid4()
        cal_id = _calibracao_aguardando_2a(repo, executor, revisor)
        with pytest.raises(FraudeConferenteEhRevisorOuExecutor):
            aprovar_2a_executar(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal_id,
                    revision_esperada=4,
                    conferente_id=executor,  # colide com executor
                    snapshot_competencia_conferente_json=_competencia_json(),
                ),
                repo,
            )

    def test_conferente_eh_revisor_com_excecao_adr0026_completa_aceita(self) -> None:
        """Excecao ADR-0026: conferente == revisor permitido SE excecao_motivo
        + excecao_2a_conf_id fornecidos. Caller registra Excecao2aConferencia
        e passa FK."""
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        revisor = uuid4()
        excecao_id = uuid4()
        cal_id = _calibracao_aguardando_2a(repo, executor, revisor)
        out = aprovar_2a_executar(
            Aprovar2aConferenciaInput(
                calibracao_id=cal_id,
                revision_esperada=4,
                conferente_id=revisor,
                snapshot_competencia_conferente_json=_competencia_json(),
                excecao_motivo="TENANT_PEQUENO_5_CAL_MES",
                excecao_2a_conf_id=excecao_id,
            ),
            repo,
        )
        assert out.snapshot.status == EstadoCalibracao.APROVADA
        assert out.snapshot.excecao_2a_conf_id == excecao_id

    def test_excecao_motivo_sem_fk_recusa(self) -> None:
        with pytest.raises(ValueError, match="excecao_2a_conf_id"):
            Aprovar2aConferenciaInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                conferente_id=uuid4(),
                snapshot_competencia_conferente_json=_competencia_json(),
                excecao_motivo="TENANT_PEQUENO_5_CAL_MES",
                excecao_2a_conf_id=None,
            )

    def test_fk_sem_excecao_motivo_recusa(self) -> None:
        with pytest.raises(ValueError, match="excecao_motivo"):
            Aprovar2aConferenciaInput(
                calibracao_id=uuid4(),
                revision_esperada=0,
                conferente_id=uuid4(),
                snapshot_competencia_conferente_json=_competencia_json(),
                excecao_motivo=None,
                excecao_2a_conf_id=uuid4(),
            )

    def test_excecao_motivo_fora_whitelist_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        revisor = uuid4()
        cal_id = _calibracao_aguardando_2a(repo, executor, revisor)
        with pytest.raises(ExcecaoAdr0026Invalida):
            aprovar_2a_executar(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal_id,
                    revision_esperada=4,
                    conferente_id=revisor,
                    snapshot_competencia_conferente_json=_competencia_json(),
                    excecao_motivo="MOTIVO_FAKE_QUALQUER",
                    excecao_2a_conf_id=uuid4(),
                ),
                repo,
            )

    def test_estado_em_execucao_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        cal_id = _calibracao_em_execucao(repo, executor)
        with pytest.raises(
            EstadoInvalidoParaAprovar2aConferencia, match="AGUARDANDO_2A_CONFERENCIA"
        ):
            aprovar_2a_executar(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal_id,
                    revision_esperada=2,
                    conferente_id=uuid4(),
                    snapshot_competencia_conferente_json=_competencia_json(),
                ),
                repo,
            )

    def test_calibracao_sem_revisor_bloqueia(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        cal_id = _calibracao_em_revisao(repo, executor)
        # Forca status AGUARDANDO_2A_CONFERENCIA sem revisor cravado
        from dataclasses import replace

        snap = repo.snapshots[cal_id]
        repo.snapshots[cal_id] = replace(
            snap,
            status=EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA,
            revisor_id=None,
        )
        with pytest.raises(
            EstadoInvalidoParaAprovar2aConferencia, match="executor_id\\+revisor_id"
        ):
            aprovar_2a_executar(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal_id,
                    revision_esperada=3,
                    conferente_id=uuid4(),
                    snapshot_competencia_conferente_json=_competencia_json(),
                ),
                repo,
            )

    def test_aprovada_eh_estado_terminal_segunda_chamada_recusa(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        revisor = uuid4()
        conferente = uuid4()
        cal_id = _calibracao_aguardando_2a(repo, executor, revisor)
        # 1a aprovacao
        aprovar_2a_executar(
            Aprovar2aConferenciaInput(
                calibracao_id=cal_id,
                revision_esperada=4,
                conferente_id=conferente,
                snapshot_competencia_conferente_json=_competencia_json(),
            ),
            repo,
        )
        # 2a chamada — esta APROVADA agora
        with pytest.raises(
            EstadoInvalidoParaAprovar2aConferencia, match="AGUARDANDO_2A_CONFERENCIA"
        ):
            aprovar_2a_executar(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal_id,
                    revision_esperada=5,
                    conferente_id=uuid4(),
                    snapshot_competencia_conferente_json=_competencia_json(),
                ),
                repo,
            )

    def test_conflito_versao(self) -> None:
        repo = FakeCalibracaoRepository()
        executor = uuid4()
        revisor = uuid4()
        cal_id = _calibracao_aguardando_2a(repo, executor, revisor)
        with pytest.raises(ConflitoVersaoCalibracao):
            aprovar_2a_executar(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal_id,
                    revision_esperada=99,
                    conferente_id=uuid4(),
                    snapshot_competencia_conferente_json=_competencia_json(),
                ),
                repo,
            )


# =====================================================================
# Fluxo completo (smoke E2E em memoria)
# =====================================================================


def test_fluxo_completo_em_execucao_ate_aprovada() -> None:
    """Smoke: recepcao -> configurada -> em_execucao -> em_revisao_1 ->
    aguardando_2a -> APROVADA (3 atores distintos, happy path)."""
    repo = FakeCalibracaoRepository()
    executor = uuid4()
    revisor = uuid4()
    conferente = uuid4()
    cal_id = _calibracao_aguardando_2a(repo, executor, revisor)
    out = aprovar_2a_executar(
        Aprovar2aConferenciaInput(
            calibracao_id=cal_id,
            revision_esperada=4,
            conferente_id=conferente,
            snapshot_competencia_conferente_json=_competencia_json("temperatura"),
        ),
        repo,
    )
    assert out.snapshot.status == EstadoCalibracao.APROVADA
    assert out.snapshot.status.terminal
    assert out.snapshot.executor_id == executor
    assert out.snapshot.revisor_id == revisor
    assert out.snapshot.conferente_id == conferente
    assert (
        out.snapshot.snapshot_competencia_conferente_json is not None
        and out.snapshot.snapshot_competencia_conferente_json["grandeza"]
        == "temperatura"
    )
