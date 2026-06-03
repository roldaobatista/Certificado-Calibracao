"""Consolidação GATE-OS-GRANDEZA — wire-in competência do executor + propagação da
grandeza no `configurar_calibracao` (ADR-0063 Opção A / cl. 6.2.1). TST-005 puro.

Reusa o harness M4/M7. Portas `competencia_executor` (valida o técnico atribuído) e
`propagar_grandeza` (UPDATE AtividadeDaOS.grandeza) injetadas via Fake. Cobre: RBC com
competência configura; RBC sem competência → 422 ExecutorSemCompetencia; NÃO-RBC sem
grandeza nunca valida; propagação só com atividade_os_id; default lazy não bloqueia;
fallback AVULSA usa capacidade_tecnica_confirmada_por_user_id.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.application.metrologia.calibracao.configurar_calibracao import (
    ExecutorSemCompetencia,
    executar,
)
from src.domain.metrologia.calibracao.enums import EstadoCalibracao, TipoAcreditacao

from tests.test_m4_uc_configurar_calibracao import (
    _criar_calibracao_avulsa,
    _criar_calibracao_os,
    _input_avulsa,
)
from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository
from tests.test_m7_wire_in_configurar_p3 import _input_rbc


class FakeCompetencia:
    def __init__(self, ok: bool = True, motivo: str = "") -> None:
        self.ok, self.motivo, self.chamadas = ok, motivo, []

    def __call__(self, **kw) -> tuple[bool, str]:
        self.chamadas.append(kw)
        return self.ok, self.motivo


class FakePropagar:
    def __init__(self) -> None:
        self.chamadas: list[dict] = []

    def __call__(self, **kw) -> None:
        self.chamadas.append(kw)


def _competencia_explode(**_kw):
    raise AssertionError("competencia_executor NAO deveria ser chamada aqui")


def _input_os_rbc(cal_id, **over):
    # ATIVIDADE_OS exige analise_critica_pedido_id + inline_hash vazio.
    base = {"analise_critica_pedido_id": uuid4(), "analise_critica_pedido_inline_hash": ""}
    base.update(over)
    return _input_rbc(cal_id, **base)


class TestCompetenciaExecutor:
    def test_rbc_competencia_cobre_configura(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        comp = FakeCompetencia(ok=True)
        out = executar(_input_rbc(cal_id), repo, competencia_executor=comp)
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA
        assert len(comp.chamadas) == 1
        assert comp.chamadas[0]["grandeza"] == "massa"

    def test_rbc_competencia_nao_cobre_bloqueia_422(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        comp = FakeCompetencia(ok=False, motivo="rt_competencia_grandeza_nao_coberta")
        with pytest.raises(ExecutorSemCompetencia) as exc:
            executar(_input_rbc(cal_id), repo, competencia_executor=comp)
        assert exc.value.grandeza == "massa"
        assert exc.value.motivo == "rt_competencia_grandeza_nao_coberta"

    def test_nao_rbc_sem_grandeza_nao_valida(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.NAO_RBC)
        # _competencia_explode levantaria se chamado — NÃO-RBC sem grandeza não valida.
        out = executar(_input_avulsa(cal_id), repo, competencia_executor=_competencia_explode)
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA

    def test_fallback_avulsa_usa_capacidade_confirmada(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        comp = FakeCompetencia(ok=True)
        inp = _input_rbc(cal_id)
        executar(inp, repo, competencia_executor=comp)
        # AVULSA: atividade None, fallback = capacidade_tecnica_confirmada_por_user_id.
        assert comp.chamadas[0]["atividade_os_id"] is None
        assert comp.chamadas[0]["executor_fallback_id"] == inp.capacidade_tecnica_confirmada_por_user_id

    def test_default_lazy_nao_bloqueia(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        out = executar(_input_rbc(cal_id), repo)  # default fail-open lazy
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA


class TestPropagacaoGrandeza:
    def test_propaga_grandeza_para_atividade(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_os(repo)  # origem ATIVIDADE_OS (atividade_os_id set)
        prop = FakePropagar()
        # NÃO-RBC com grandeza declarada → propaga sem validar competência.
        out = executar(
            _input_os_rbc(cal_id, escopo_id=None),
            repo,
            propagar_grandeza=prop,
        )
        # ATIVIDADE_OS NÃO-RBC: grandeza declarada dispara a propagação.
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA
        assert len(prop.chamadas) == 1
        assert prop.chamadas[0]["grandeza"] == "massa"
        assert prop.chamadas[0]["atividade_os_id"] is not None

    def test_avulsa_nao_propaga(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        prop = FakePropagar()
        executar(_input_rbc(cal_id), repo, propagar_grandeza=prop)
        assert prop.chamadas == []  # AVULSA: atividade_os_id None → não propaga
