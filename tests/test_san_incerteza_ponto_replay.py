"""SAN-INCERTEZA-PONTO — replay determinismo cl. 7.11 (ADR-0025/ADR-0077).

Golden-file: a mesma entrada (componentes base + repeticoes por ponto +
versao_motor) reproduz EXATAMENTE u_c, U(ponto), k, dof, metodo Tipo A, s
aplicado, hash por ponto, hash agregado e cadeia de fecho. Pega regressao no
motor de calculo por ponto — qualquer alteracao no resultado quebra aqui e exige
reanalise metrologica (consultor-rbc) + revalidacao cl. 7.11 (ver `_aceite_motivo`
no fixture). Puro (sem Django/PG): o hash NAO depende de tenant_id/orcamento_id.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from src.application.metrologia.calibracao.calcular_orcamento_incerteza import (
    CalcularOrcamentoIncertezaInput,
    ComponenteParaCalculo,
    PontoParaCalculo,
    executar,
)
from src.domain.metrologia.calibracao.enums import (
    DistribuicaoIncerteza,
    EstadoCalibracao,
    FormulaCalculoComponente,
    LeiEscalonamento,
    MetodoTipoAPonto,
    TipoOrigemComponente,
)

_FIXTURE = Path(__file__).parent / "replay_metrologico" / "orcamento_por_ponto.json"
_CAL_ID = UUID("11111111-1111-1111-1111-111111111111")
_TENANT = UUID("22222222-2222-2222-2222-222222222222")


@dataclass(frozen=True)
class _CalStub:
    """Snapshot minimo de calibracao (duck-typing — use case lê só status/tenant)."""

    tenant_id: UUID = _TENANT
    status: EstadoCalibracao = EstadoCalibracao.EM_EXECUCAO


@dataclass
class _FakeCal:
    def obter_por_id(self, _id: UUID) -> _CalStub:
        return _CalStub()


@dataclass
class _FakeOrc:
    def salvar_orcamento_com_componentes(self, o: object, c: object, pontos: object = ()) -> None:
        return None

    def obter_por_id(self, _id: UUID) -> None:
        return None

    def listar_componentes(self, _id: UUID) -> list:
        return []


def _componente_do_fixture(d: dict) -> ComponenteParaCalculo:
    return ComponenteParaCalculo(
        nome=d["nome"],
        tipo="B",
        u_i=Decimal(d["u_i"]),
        grau_liberdade=None,
        tipo_origem_componente=TipoOrigemComponente[d["tipo_origem"]],
        distribuicao=DistribuicaoIncerteza[d["distribuicao"]],
        divisor=Decimal(d["divisor"]),
        formula_calculo=FormulaCalculoComponente[d["formula"]],
        lei_escalonamento=LeiEscalonamento[d["lei"]],
    )


def _ponto_do_fixture(d: dict) -> PontoParaCalculo:
    s_pooled = None
    if d["s_pooled"] is not None:
        s_pooled = (Decimal(d["s_pooled"][0]), int(d["s_pooled"][1]))
    return PontoParaCalculo(
        ponto_calibracao=Decimal(d["ponto"]),
        valores_repeticoes=tuple(Decimal(v) for v in d["repeticoes"]),
        s_pooled=s_pooled,
    )


def _rodar_do_fixture(dados: dict):
    entrada = dados["entrada"]
    inp = CalcularOrcamentoIncertezaInput(
        calibracao_id=_CAL_ID,
        componentes=tuple(
            _componente_do_fixture(c) for c in entrada["componentes_base"]
        ),
        correlacoes=(),
        versao_motor_calculo=entrada["versao_motor_calculo"],
        documentacao_agregacao=entrada["documentacao_agregacao"],
        bias_orcado=None,
        bias_origem="",
        calculado_em=datetime(2026, 5, 26, 16, 0, tzinfo=UTC),
        correlation_id=UUID("33333333-3333-3333-3333-333333333333"),
        pontos=tuple(_ponto_do_fixture(p) for p in entrada["pontos"]),
        perfil_tenant=entrada["perfil_tenant"],
    )
    return executar(inp, _FakeCal(), _FakeOrc())


class TestReplayPorPonto:
    def test_pontos_batem_ground_truth(self) -> None:
        dados = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        out = _rodar_do_fixture(dados)
        # ordena por ponto para casar com o esperado (que está em ordem ASC)
        pontos = sorted(out.pontos, key=lambda p: p.ponto_calibracao)
        esperado = sorted(dados["esperado_pontos"], key=lambda e: Decimal(e["ponto"]))
        assert len(pontos) == len(esperado)
        for p, e in zip(pontos, esperado, strict=True):
            assert str(p.ponto_calibracao) == e["ponto"]
            assert p.metodo_tipo_a_ponto is MetodoTipoAPonto[e["metodo"]]
            assert p.n_repeticoes_ponto == e["n"]
            assert str(p.u_combinada_no_ponto) == e["u_combinada"]
            assert str(p.U_expandida_no_ponto) == e["U_expandida"]
            assert str(p.k_no_ponto) == e["k"]
            assert str(p.grau_liberdade_efetivo_no_ponto) == e["dof"]
            assert str(p.s_tipo_a_no_ponto) == e["s_tipo_a"]
            assert p.replay_determinismo_hash_no_ponto == e["hash"]

    def test_agregado_bate_ground_truth(self) -> None:
        dados = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        out = _rodar_do_fixture(dados)
        esp = dados["esperado_agregado"]
        assert str(out.orcamento.U_expandida) == esp["U_expandida"]
        assert str(out.orcamento.u_combinada) == esp["u_combinada"]
        assert str(out.orcamento.k) == esp["k"]
        assert (
            out.orcamento.algoritmo_1_resultado["ponto_pior_caso"]
            == esp["ponto_pior_caso"]
        )
        assert out.orcamento.replay_determinismo_hash == esp["replay_determinismo_hash"]
        assert out.orcamento.cadeia_pontos_hash == esp["cadeia_pontos_hash"]

    def test_replay_idempotente(self) -> None:
        """Rodar 2x a mesma entrada -> mesmos hashes (determinismo cl. 7.11)."""
        dados = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        out1 = _rodar_do_fixture(dados)
        out2 = _rodar_do_fixture(dados)
        assert (
            out1.orcamento.cadeia_pontos_hash == out2.orcamento.cadeia_pontos_hash
        )
        assert [p.replay_determinismo_hash_no_ponto for p in out1.pontos] == [
            p.replay_determinismo_hash_no_ponto for p in out2.pontos
        ]
