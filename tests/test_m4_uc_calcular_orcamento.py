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
    ComponenteParaCalculo,
    EscalonamentoNaoSuportadoError,
    PontoParaCalculo,
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
    OrcamentoPorPontoSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    DistribuicaoIncerteza,
    EstadoCalibracao,
    FormulaCalculoComponente,
    LeiEscalonamento,
    MetodoTipoAPonto,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
    TipoOrigemComponente,
)
from src.domain.metrologia.calibracao.motor_calculo.incerteza_por_ponto import (
    TipoAAusenteError,
    TipoAInsuficienteError,
)

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository

# =====================================================================
# Helpers de componente (proveniencia §16.6 — GATE-CAL-DOMAIN-MODEL-DRIFT)
# =====================================================================


def _comp_tipo_a(
    nome: str = "repetibilidade",
    u_i: str = "0.01",
    n_amostras: int = 10,
    s_x: str = "0.0316",
) -> ComponenteParaCalculo:
    """Componente Tipo A com s_x + n>=6 (CHECK ck_componente_tipo_a_n_min)."""
    return ComponenteParaCalculo(
        nome=nome,
        tipo="A",
        u_i=Decimal(u_i),
        grau_liberdade=None,  # derivado de n-1
        tipo_origem_componente=TipoOrigemComponente.REPETIBILIDADE,
        distribuicao=DistribuicaoIncerteza.NORMAL,
        divisor=Decimal("1.00000"),
        formula_calculo=FormulaCalculoComponente.REPETIBILIDADE_STD_MEDIA,
        s_x=Decimal(s_x),
        n_amostras=n_amostras,
    )


def _comp_tipo_b(
    nome: str,
    u_i: str,
    origem: TipoOrigemComponente = TipoOrigemComponente.RESOLUCAO_INSTRUMENTO,
    distribuicao: DistribuicaoIncerteza = DistribuicaoIncerteza.RETANGULAR,
    divisor: str = "1.73205",
    formula: FormulaCalculoComponente = FormulaCalculoComponente.RESOLUCAO_RETANGULAR,
) -> ComponenteParaCalculo:
    """Componente Tipo B (u_i declarado direto, dof infinito)."""
    return ComponenteParaCalculo(
        nome=nome,
        tipo="B",
        u_i=Decimal(u_i),
        grau_liberdade=None,
        tipo_origem_componente=origem,
        distribuicao=distribuicao,
        divisor=Decimal(divisor),
        formula_calculo=formula,
    )

# =====================================================================
# FakeOrcamentoIncertezaRepository
# =====================================================================


@dataclass
class FakeOrcamentoIncertezaRepository:
    orcamentos: dict[UUID, OrcamentoIncertezaSnapshot] = field(default_factory=dict)
    _componentes_por_orcamento: dict[UUID, list[ComponenteIncertezaSnapshot]] = field(
        default_factory=dict
    )
    _pontos_por_orcamento: dict[UUID, list[OrcamentoPorPontoSnapshot]] = field(
        default_factory=dict
    )

    def salvar_orcamento_com_componentes(
        self,
        orcamento: OrcamentoIncertezaSnapshot,
        componentes: list[ComponenteIncertezaSnapshot],
        pontos: tuple[OrcamentoPorPontoSnapshot, ...] = (),
    ) -> None:
        if orcamento.id in self.orcamentos:
            raise ValueError(f"orcamento duplicado {orcamento.id}")
        self.orcamentos[orcamento.id] = orcamento
        self._componentes_por_orcamento[orcamento.id] = list(componentes)
        self._pontos_por_orcamento[orcamento.id] = list(pontos)

    def obter_por_id(self, orcamento_id: UUID) -> OrcamentoIncertezaSnapshot | None:
        return self.orcamentos.get(orcamento_id)

    def listar_componentes(
        self, orcamento_id: UUID
    ) -> list[ComponenteIncertezaSnapshot]:
        return list(self._componentes_por_orcamento.get(orcamento_id, ()))

    def listar_pontos(
        self, orcamento_id: UUID
    ) -> list[OrcamentoPorPontoSnapshot]:
        return list(self._pontos_por_orcamento.get(orcamento_id, ()))


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
            _comp_tipo_a("repetibilidade", u_i="0.01", n_amostras=10),
            _comp_tipo_b("resolucao", u_i="0.005"),
            _comp_tipo_b(
                "padrao",
                u_i="0.002",
                origem=TipoOrigemComponente.INCERTEZA_PADRAO_REF,
                distribuicao=DistribuicaoIncerteza.NORMAL,
                divisor="2.00000",
                formula=FormulaCalculoComponente.PADRAO_CERTIFICADO,
            ),
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
                _comp_tipo_a("a", u_i="0.01", n_amostras=10),
                _comp_tipo_b("b", u_i="0.005"),
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


# =====================================================================
# Proveniencia §16.6 (GATE-CAL-DOMAIN-MODEL-DRIFT)
# =====================================================================


class TestProveniencia16_6:
    def test_componentes_carregam_proveniencia_no_snapshot(self) -> None:
        """tipo_origem/distribuicao/divisor/formula propagam pro snapshot."""
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        rep = next(
            c for c in out.componentes_persistidos if c.nome_componente == "repetibilidade"
        )
        assert rep.tipo_origem_componente == TipoOrigemComponente.REPETIBILIDADE
        assert rep.distribuicao == DistribuicaoIncerteza.NORMAL
        assert rep.divisor == Decimal("1.00000")
        assert rep.formula_calculo == FormulaCalculoComponente.REPETIBILIDADE_STD_MEDIA

    def test_tipo_a_carrega_s_x_nao_nulo(self) -> None:
        """Tipo A grava s_x (CHECK ck_componente_tipo_a_n_min)."""
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        comp_a = next(c for c in out.componentes_persistidos if c.tipo_componente == "A")
        assert comp_a.s_x is not None
        assert comp_a.n_amostras is not None and comp_a.n_amostras >= 6


class TestValidacaoComponenteParaCalculo:
    def test_tipo_a_sem_s_x_rejeita(self) -> None:
        with pytest.raises(ValueError, match="s_x NOT NULL"):
            ComponenteParaCalculo(
                nome="rep",
                tipo="A",
                u_i=Decimal("0.01"),
                grau_liberdade=9,
                tipo_origem_componente=TipoOrigemComponente.REPETIBILIDADE,
                distribuicao=DistribuicaoIncerteza.NORMAL,
                divisor=Decimal("1"),
                formula_calculo=FormulaCalculoComponente.REPETIBILIDADE_STD_MEDIA,
                s_x=None,
                n_amostras=10,
            )

    def test_tipo_a_n_menor_que_6_rejeita(self) -> None:
        with pytest.raises(ValueError, match="n_amostras >= 6"):
            _comp_tipo_a(n_amostras=5)

    def test_divisor_zero_rejeita(self) -> None:
        with pytest.raises(ValueError, match="divisor deve ser > 0"):
            _comp_tipo_b("x", u_i="0.01", divisor="0")

    def test_correlacao_sem_coeficiente_rejeita(self) -> None:
        with pytest.raises(ValueError, match="INV-CAL-INC-004"):
            ComponenteParaCalculo(
                nome="x",
                tipo="B",
                u_i=Decimal("0.01"),
                grau_liberdade=None,
                tipo_origem_componente=TipoOrigemComponente.OUTRO,
                distribuicao=DistribuicaoIncerteza.OUTRA,
                divisor=Decimal("1"),
                formula_calculo=FormulaCalculoComponente.OUTRO,
                correlacao_com_componente_id=uuid4(),
                coeficiente_correlacao=None,
            )

    def test_tipo_a_grau_liberdade_derivado_de_n(self) -> None:
        """grau_liberdade omitido -> n-1 (consistencia GUM)."""
        comp = _comp_tipo_a(n_amostras=10)
        assert comp.grau_liberdade == 9


def test_repository_protocol_compativel() -> None:
    """FakeOrcamentoIncertezaRepository implementa o Protocol."""
    from src.domain.metrologia.calibracao.repository import (
        OrcamentoIncertezaRepository,
    )

    repo = FakeOrcamentoIncertezaRepository()
    assert isinstance(repo, OrcamentoIncertezaRepository)


# =====================================================================
# Modo por-ponto (ADR-0077 / SAN-INCERTEZA-PONTO)
# =====================================================================


def _reps(base: str, spread: str, n: int = 6) -> tuple[Decimal, ...]:
    """n repeticoes centradas em `base`; amplitude ~`spread` (s_x cresce c/ spread)."""
    b = Decimal(base)
    s = Decimal(spread)
    deltas = [Decimal(0), s, -s, s / 2, -s / 2, Decimal(0)][:n]
    return tuple(b + d for d in deltas)


def _comp_b_padrao(lei: LeiEscalonamento = LeiEscalonamento.CONSTANTE) -> ComponenteParaCalculo:
    return ComponenteParaCalculo(
        nome="padrao",
        tipo="B",
        u_i=Decimal("0.002"),
        grau_liberdade=None,
        tipo_origem_componente=TipoOrigemComponente.INCERTEZA_PADRAO_REF,
        distribuicao=DistribuicaoIncerteza.NORMAL,
        divisor=Decimal("2.00000"),
        formula_calculo=FormulaCalculoComponente.PADRAO_CERTIFICADO,
        lei_escalonamento=lei,
    )


def _input_por_ponto(
    calibracao_id: UUID,
    pontos: tuple[PontoParaCalculo, ...],
    *,
    perfil: str = "A",
    componentes: tuple[ComponenteParaCalculo, ...] | None = None,
    **overrides: object,
) -> CalcularOrcamentoIncertezaInput:
    comps = componentes if componentes is not None else (
        _comp_tipo_b("resolucao", u_i="0.005"),
        _comp_b_padrao(),
    )
    defaults: dict[str, object] = {
        "calibracao_id": calibracao_id,
        "componentes": comps,
        "correlacoes": (),
        "versao_motor_calculo": "1.0.0+abc123",
        "documentacao_agregacao": (
            "Orcamento por ponto NIT-DICLA-030 rev. 15. Tipo A derivado por "
            "ponto das repeticoes via GUM cl. 4.2; agregado pior-caso."
        ),
        "bias_orcado": None,
        "bias_origem": "",
        "calculado_em": datetime(2026, 5, 26, 16, 0, tzinfo=UTC),
        "correlation_id": uuid4(),
        "pontos": pontos,
        "perfil_tenant": perfil,
    }
    defaults.update(overrides)
    return CalcularOrcamentoIncertezaInput(**defaults)  # type: ignore[arg-type]


# 3 pontos com s_x crescente -> U cresce -> j* = ponto 100.
_TRES_PONTOS = (
    PontoParaCalculo(Decimal("10"), _reps("10", "0.01")),
    PontoParaCalculo(Decimal("50"), _reps("50", "0.05")),
    PontoParaCalculo(Decimal("100"), _reps("100", "0.10")),
)


class TestPorPontoHappy:
    def test_produz_n_orcamentos_por_ponto(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_por_ponto(cal_id, _TRES_PONTOS), cal_repo, orc_repo)
        assert len(out.pontos) == 3
        assert all(
            p.metodo_tipo_a_ponto is MetodoTipoAPonto.SX_PROPRIO for p in out.pontos
        )
        assert all(p.n_repeticoes_ponto == 6 for p in out.pontos)
        assert all(p.s_tipo_a_no_ponto is not None for p in out.pontos)
        # persistido via repo
        assert orc_repo.listar_pontos(out.orcamento.id) == list(out.pontos)

    def test_agregado_e_pior_caso_max_U(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_por_ponto(cal_id, _TRES_PONTOS), cal_repo, orc_repo)
        max_u = max(p.U_expandida_no_ponto for p in out.pontos)
        assert out.orcamento.U_expandida == max_u
        # j* = ponto de maior U (ponto 100, maior spread)
        j = max(out.pontos, key=lambda p: p.U_expandida_no_ponto)
        assert j.ponto_calibracao == Decimal("100")
        # coerencia: global espelha o ponto j* (u_c bruto + replay hash)
        assert out.orcamento.u_combinada == j.u_combinada_no_ponto
        assert (
            out.orcamento.replay_determinismo_hash
            == j.replay_determinismo_hash_no_ponto
        )

    def test_global_persiste_so_tipo_b(self) -> None:
        """Decisao tech-lead (a): Tipo A NAO vira ComponenteIncerteza global."""
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_por_ponto(cal_id, _TRES_PONTOS), cal_repo, orc_repo)
        assert len(out.componentes_persistidos) == 2
        assert all(c.tipo_componente == "B" for c in out.componentes_persistidos)

    def test_cadeia_pontos_hash_versionado(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_por_ponto(cal_id, _TRES_PONTOS), cal_repo, orc_repo)
        assert out.orcamento.cadeia_pontos_hash.startswith("v01$")
        assert len(out.orcamento.cadeia_pontos_hash) == len("v01$") + 44

    def test_algoritmo_1_marca_modo_por_ponto(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_por_ponto(cal_id, _TRES_PONTOS), cal_repo, orc_repo)
        assert out.orcamento.algoritmo_1_resultado["modo"] == "por_ponto"
        assert out.orcamento.algoritmo_1_resultado["n_pontos"] == 3
        assert out.orcamento.algoritmo_1_resultado["ponto_pior_caso"] == "100"


class TestPorPontoBackwardCompat:
    def test_path_flat_sem_pontos_intacto(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        out = executar(_input_calculo(cal_id), cal_repo, orc_repo)
        assert out.pontos == ()
        assert out.orcamento.cadeia_pontos_hash == ""


class TestPorPontoDeterminismo:
    def test_ordem_dos_pontos_nao_muda_cadeia_nem_agregado(self) -> None:
        cal_repo_a = FakeCalibracaoRepository()
        cal_repo_b = FakeCalibracaoRepository()
        orc_a = FakeOrcamentoIncertezaRepository()
        orc_b = FakeOrcamentoIncertezaRepository()
        cal_a = _calibracao_em_execucao(cal_repo_a)
        cal_b = _calibracao_em_execucao(cal_repo_b)
        pontos_ordem_1 = _TRES_PONTOS
        pontos_ordem_2 = (_TRES_PONTOS[2], _TRES_PONTOS[0], _TRES_PONTOS[1])
        out_a = executar(_input_por_ponto(cal_a, pontos_ordem_1), cal_repo_a, orc_a)
        out_b = executar(_input_por_ponto(cal_b, pontos_ordem_2), cal_repo_b, orc_b)
        assert out_a.orcamento.cadeia_pontos_hash == out_b.orcamento.cadeia_pontos_hash
        assert out_a.orcamento.U_expandida == out_b.orcamento.U_expandida
        assert (
            out_a.orcamento.replay_determinismo_hash
            == out_b.orcamento.replay_determinismo_hash
        )


class TestPorPontoValidacaoInput:
    def test_pontos_sem_perfil_rejeita(self) -> None:
        with pytest.raises(ValueError, match="perfil_tenant"):
            _input_por_ponto(uuid4(), _TRES_PONTOS, perfil="")

    def test_componentes_tipo_a_no_modo_por_ponto_rejeita(self) -> None:
        with pytest.raises(ValueError, match="so Tipo B"):
            _input_por_ponto(uuid4(), _TRES_PONTOS, componentes=(_comp_tipo_a(),))

    def test_ponto_valor_float_rejeita(self) -> None:
        with pytest.raises(TypeError, match="valores_repeticoes"):
            PontoParaCalculo(Decimal("10"), (0.5,))  # type: ignore[arg-type]


class TestPorPontoFailClosedPerfilA:
    def _ponto_n3(self) -> tuple[PontoParaCalculo, ...]:
        return (
            PontoParaCalculo(
                Decimal("10"), (Decimal("10"), Decimal("10.1"), Decimal("9.9"))
            ),
        )

    def test_n_entre_2_e_6_sem_pool_perfil_A_bloqueia_atomico(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        with pytest.raises(TipoAInsuficienteError):
            executar(
                _input_por_ponto(cal_id, self._ponto_n3(), perfil="A"),
                cal_repo,
                orc_repo,
            )
        assert orc_repo.orcamentos == {}  # nada persistido (atomico)

    def test_ausente_perfil_A_bloqueia(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        pontos = (PontoParaCalculo(Decimal("10"), (Decimal("10"),)),)
        with pytest.raises(TipoAAusenteError):
            executar(
                _input_por_ponto(cal_id, pontos, perfil="A"), cal_repo, orc_repo
            )

    def test_indicacao_unica_com_pool_emite(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        pontos = (
            PontoParaCalculo(
                Decimal("10"), (Decimal("10"),), s_pooled=(Decimal("0.02"), 40)
            ),
        )
        out = executar(_input_por_ponto(cal_id, pontos, perfil="A"), cal_repo, orc_repo)
        assert out.pontos[0].metodo_tipo_a_ponto is MetodoTipoAPonto.S_POOLED
        assert out.pontos[0].s_tipo_a_no_ponto == Decimal("0.02")
        assert out.pontos[0].n_repeticoes_ponto == 1


class TestPorPontoRessalvaNaoA:
    @pytest.mark.parametrize("perfil", ["B", "C", "D"])
    def test_n_entre_2_e_6_sem_pool_ressalva_nao_bloqueia(self, perfil: str) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        pontos = (
            PontoParaCalculo(
                Decimal("10"), (Decimal("10"), Decimal("10.1"), Decimal("9.9"))
            ),
        )
        out = executar(
            _input_por_ponto(cal_id, pontos, perfil=perfil), cal_repo, orc_repo
        )
        assert out.pontos[0].tipo_a_insuficiente is True
        assert out.pontos[0].metodo_tipo_a_ponto is MetodoTipoAPonto.SX_PROPRIO


class TestPorPontoEscalonamento:
    def test_b_diferente_de_constante_perfil_A_fail_closed(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        comps = (_comp_b_padrao(lei=LeiEscalonamento.PROPORCIONAL),)
        pontos = (PontoParaCalculo(Decimal("10"), _reps("10", "0.01")),)
        with pytest.raises(EscalonamentoNaoSuportadoError):
            executar(
                _input_por_ponto(cal_id, pontos, perfil="A", componentes=comps),
                cal_repo,
                orc_repo,
            )
        assert orc_repo.orcamentos == {}

    def test_b_diferente_de_constante_perfil_C_registra_ressalva(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        orc_repo = FakeOrcamentoIncertezaRepository()
        cal_id = _calibracao_em_execucao(cal_repo)
        comps = (_comp_b_padrao(lei=LeiEscalonamento.PROPORCIONAL),)
        pontos = (PontoParaCalculo(Decimal("10"), _reps("10", "0.01")),)
        out = executar(
            _input_por_ponto(cal_id, pontos, perfil="C", componentes=comps),
            cal_repo,
            orc_repo,
        )
        assert (
            out.pontos[0].lei_escalonamento_aplicada is LeiEscalonamento.PROPORCIONAL
        )
