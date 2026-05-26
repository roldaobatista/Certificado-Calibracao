"""Testes use case calcular_orcamento_incerteza (P4 Fase 5 Batch E — T-CAL-091).

Orquestra motor_calculo.gum_classico.propagar + arredondamento NIT-DICLA-030
+ canonicalizar + persistencia.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.calcular_orcamento_incerteza import (
    CalcularOrcamentoIncertezaInput,
    CalibracaoEstadoNaoPermiteCalcular,
    executar,
)
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
from src.domain.metrologia.calibracao.entities import (
    ComponenteIncertezaSnapshot,
    OrcamentoIncertezaSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.motor_calculo.gum_classico import (
    ComponenteEntrada,
)

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository

# =====================================================================
# FakeOrcamentoIncertezaRepository
# =====================================================================


@dataclass
class FakeOrcamentoIncertezaRepository:
    orcamentos: dict[UUID, OrcamentoIncertezaSnapshot] = field(default_factory=dict)
    _componentes_por_orcamento: dict[UUID, list[ComponenteIncertezaSnapshot]] = field(
        default_factory=dict
    )

    def salvar_orcamento_com_componentes(
        self,
        orcamento: OrcamentoIncertezaSnapshot,
        componentes: list[ComponenteIncertezaSnapshot],
    ) -> None:
        if orcamento.id in self.orcamentos:
            raise ValueError(f"orcamento duplicado {orcamento.id}")
        self.orcamentos[orcamento.id] = orcamento
        self._componentes_por_orcamento[orcamento.id] = list(componentes)

    def obter_por_id(self, orcamento_id: UUID) -> OrcamentoIncertezaSnapshot | None:
        return self.orcamentos.get(orcamento_id)

    def listar_componentes(
        self, orcamento_id: UUID
    ) -> list[ComponenteIncertezaSnapshot]:
        return list(self._componentes_por_orcamento.get(orcamento_id, ()))


# =====================================================================
# Helpers
# =====================================================================


def _calibracao_em_execucao(repo: FakeCalibracaoRepository) -> UUID:
    """Cria+configura+inicia calibracao; retorna id (EM_EXECUCAO)."""
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
                "codigo": "PRO-CAL-MASSA",
                "versao": "1.0.0",
                "hash_anexo": "v01$abc=",
            },
            regra_decisao=RegraDecisao.BANDA_GUARDA_30,
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


def _input_calculo(calibracao_id: UUID, **overrides: object) -> CalcularOrcamentoIncertezaInput:
    defaults: dict[str, object] = {
        "calibracao_id": calibracao_id,
        "componentes": (
            ComponenteEntrada("repetibilidade", Decimal("0.01"), "A", 9),
            ComponenteEntrada("resolucao", Decimal("0.005"), "B", None),
            ComponenteEntrada("padrao", Decimal("0.002"), "B", None),
        ),
        "correlacoes": (),
        "versao_motor_calculo": "1.0.0+abc123",
        "documentacao_agregacao": (
            "Orcamento agregado conforme NIT-DICLA-030 rev. 15. "
            "Componentes Tipo A e B combinados via GUM cl. 5.1.2."
        ),
        "bias_orcado": None,
        "bias_origem": "",
        "calculado_em": datetime(2026, 5, 26, 16, 0, tzinfo=UTC),
        "correlation_id": uuid4(),
    }
    defaults.update(overrides)
    return CalcularOrcamentoIncertezaInput(**defaults)  # type: ignore[arg-type]


# =====================================================================
# Happy path
# =====================================================================


class TestHappyPath:
    def test_calcula_em_em_execucao(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        # u_c = sqrt(0.01^2 + 0.005^2 + 0.002^2) = sqrt(0.000129) ~ 0.01136
        assert Decimal("0.011") < out.orcamento.u_combinada < Decimal("0.012")
        # U_expandida arredondada (2 sig)
        assert out.orcamento.U_expandida.adjusted() <= -1  # ordem -2 (0.0XX)
        # Algoritmo 2 (Monte Carlo) NULL — DEP-001 numpy bloqueado
        assert out.orcamento.algoritmo_2_resultado is None
        assert out.orcamento.divergencia_pct is None
        # 3 componentes persistidos
        assert len(out.componentes_persistidos) == 3

    def test_replay_hash_versionado(self) -> None:
        """replay_determinismo_hash no formato v<NN>$<base64>."""
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        h = out.orcamento.replay_determinismo_hash
        assert h.startswith("v01$")
        # Base64 do SHA-256 = 44 chars (32 bytes -> 44 base64 com padding)
        assert len(h) == len("v01$") + 44

    def test_determinismo_mesma_input_mesmo_hash(self) -> None:
        """ADR-0025 cl. 7.11 — replay deterministico."""
        cal_repo_a = FakeCalibracaoRepository()
        cal_repo_b = FakeCalibracaoRepository()
        orc_a = FakeOrcamentoIncertezaRepository()
        orc_b = FakeOrcamentoIncertezaRepository()
        cal_a = _calibracao_em_execucao(cal_repo_a)
        cal_b = _calibracao_em_execucao(cal_repo_b)
        # Input identico (componentes + correlacoes + versao_motor)
        comuns: dict[str, object] = {
            "componentes": (
                ComponenteEntrada("a", Decimal("0.01"), "A", 9),
                ComponenteEntrada("b", Decimal("0.005"), "B", None),
            ),
            "versao_motor_calculo": "1.0.0+abc123",
        }
        out_a = executar(_input_calculo(cal_a, **comuns), cal_repo_a, orc_a)
        out_b = executar(_input_calculo(cal_b, **comuns), cal_repo_b, orc_b)
        # Hash deve ser identico (mesma input -> mesmo hash, sempre)
        assert out_a.orcamento.replay_determinismo_hash == out_b.orcamento.replay_determinismo_hash

    def test_arredondamento_aplicado_regra_cravada(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        assert out.orcamento.arredondamento_aplicado_regra == "NIT_DICLA_030_2_DIGITOS_SIG"

    def test_componentes_tipo_a_carregam_n_amostras(self) -> None:
        """ComponenteEntrada Tipo A com dof=9 -> n_amostras=10 no snapshot."""
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        comp_a = next(c for c in out.componentes_persistidos if c.tipo_componente == "A")
        # dof=9 + 1 = n=10
        assert comp_a.n_amostras == 10
        assert comp_a.grau_liberdade == Decimal("9")

    def test_componentes_tipo_b_sem_n_amostras(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        comps_b = [c for c in out.componentes_persistidos if c.tipo_componente == "B"]
        assert len(comps_b) == 2
        for c in comps_b:
            assert c.n_amostras is None
            assert c.grau_liberdade is None

    def test_persistencia_via_repo(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        # Reload do repo confere
        assert orc_repo.obter_por_id(out.orcamento.id) == out.orcamento
        assert orc_repo.listar_componentes(out.orcamento.id) == list(
            out.componentes_persistidos
        )

    def test_em_revisao_1_tambem_permite_recalculo(self) -> None:
        """Re-calculo apos correcao via NC eh permitido em EM_REVISAO_1."""
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        # Forca EM_REVISAO_1
        from dataclasses import replace
        snap = cal_repo.snapshots[cal_id]
        cal_repo.snapshots[cal_id] = replace(snap, status=EstadoCalibracao.EM_REVISAO_1)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        assert out.orcamento.calibracao_id == cal_id


# =====================================================================
# Validacoes input
# =====================================================================


class TestValidacoesInput:
    def test_rejeita_componentes_vazio(self) -> None:
        with pytest.raises(ValueError, match="componentes vazio"):
            _input_calculo(uuid4(), componentes=())

    def test_rejeita_documentacao_curta(self) -> None:
        with pytest.raises(ValueError, match=">= 50"):
            _input_calculo(uuid4(), documentacao_agregacao="curto")

    def test_rejeita_versao_motor_vazia(self) -> None:
        with pytest.raises(ValueError, match="versao_motor_calculo"):
            _input_calculo(uuid4(), versao_motor_calculo="")

    def test_rejeita_calculado_em_sem_tz(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            _input_calculo(uuid4(), calculado_em=datetime(2026, 5, 26, 16, 0))

    def test_rejeita_bias_float(self) -> None:
        with pytest.raises(TypeError, match="bias_orcado deve ser Decimal"):
            _input_calculo(uuid4(), bias_orcado=0.01)


# =====================================================================
# Validacoes estado
# =====================================================================


class TestEstadosCalibracao:
    def test_calibracao_nao_encontrada(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        with pytest.raises(CalibracaoNaoEncontrada):
            executar(_input_calculo(uuid4()), cal_repo, orc_repo)

    def test_recepcionada_recusa(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        criada = criar_executar(
            CriarCalibracaoInput(
                tenant_id=uuid4(),
                origem_recepcao=OrigemRecepcao.AVULSA,
                atividade_os_id=None,
                instrumento_id=uuid4(),
                snapshot_equipamento_json={"x": "y"},
                cliente_id=uuid4(),
                cliente_referencia_hash="v01$aGVsbG8=",
                cliente_key_id="k",
                tipo_acreditacao=TipoAcreditacao.NAO_RBC,
                recepcionada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
                correlation_id=uuid4(),
            ),
            cal_repo,
        )
        with pytest.raises(CalibracaoEstadoNaoPermiteCalcular):
            executar(_input_calculo(criada.snapshot.id), cal_repo, orc_repo)

    def test_aprovada_recusa(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        from dataclasses import replace
        snap = cal_repo.snapshots[cal_id]
        cal_repo.snapshots[cal_id] = replace(snap, status=EstadoCalibracao.APROVADA)
        with pytest.raises(CalibracaoEstadoNaoPermiteCalcular):
            executar(_input_calculo(cal_id), cal_repo, orc_repo)


def test_repository_protocol_compativel() -> None:
    """FakeOrcamentoIncertezaRepository implementa o Protocol."""
    from src.domain.metrologia.calibracao.repository import (
        OrcamentoIncertezaRepository,
    )

    repo = FakeOrcamentoIncertezaRepository()
    assert isinstance(repo, OrcamentoIncertezaRepository)
