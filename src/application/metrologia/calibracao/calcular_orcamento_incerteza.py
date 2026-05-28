"""Use case `calcular_orcamento_incerteza` (P4 Fase 5 Batch E — T-CAL-091).

Orquestra:
  1. motor_calculo.gum_classico.propagar(componentes, correlacoes) —
     calcula u_c, dof Welch-Satterthwaite, k_95, U_expandida em Decimal.
  2. motor_calculo.arredondamento.arredondar_2_digitos_significativos(U)
     — aplica NIT-DICLA-030 §7.5.
  3. canonicalizar_payload_para_hmac(inputs+outputs) — produz bytes
     deterministicos pra replay (ADR-0025 cl. 7.11).
  4. formatar_hash_versionado(VERSAO_HMAC_ATUAL, sha256(bytes)) — placeholder
     do HMAC-KMS real (que entra em infrastructure/calibracao/hash_kms.py).
  5. Persiste OrcamentoIncerteza + ComponentesIncerteza via Protocol.

Estados permitidos da Calibracao:
  - EM_EXECUCAO (1o calculo).
  - EM_REVISAO_1 (re-calculo apos correcao via NC fluxo separado).

INV-CAL-INC-001: documentacao_agregacao >= 50 chars.
INV-CAL-INC-003: Tipo A exige n_amostras >= 6 + s_x NOT NULL (validado em
ComponenteParaCalculo.__post_init__ — espelha CHECK ck_componente_tipo_a_n_min).
INV-CAL-INC-004: correlacao declarada exige coeficiente_correlacao.
Proveniencia §16.6 (tipo_origem/distribuicao/divisor/formula) viaja em
ComponenteParaCalculo -> snapshot persistido (GATE-CAL-DOMAIN-MODEL-DRIFT).
ADR-0025: replay_determinismo_hash garante reproducibilidade 25a.

Algoritmo 2 (Monte Carlo) BLOQUEADO DEP-001 numpy — release atual roda
SO algoritmo 1; divergencia_pct fica NULL. Quando numpy entrar, use case
chama monte_carlo.simular() + valida_replay.comparar_algoritmos().
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
)
from src.domain.metrologia.calibracao.entities import (
    ComponenteIncertezaSnapshot,
    OrcamentoIncertezaSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    DistribuicaoIncerteza,
    EstadoCalibracao,
    FormulaCalculoComponente,
    TipoOrigemComponente,
)
from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
)
from src.domain.metrologia.calibracao.motor_calculo.arredondamento import (
    REGRA_ID,
    arredondar_2_digitos_significativos,
)
from src.domain.metrologia.calibracao.motor_calculo.gum_classico import (
    ComponenteEntrada,
    propagar,
)
from src.domain.metrologia.calibracao.repository import (
    CalibracaoRepository,
    OrcamentoIncertezaRepository,
)

_ESTADOS_CALCULO_PERMITIDO: frozenset[EstadoCalibracao] = frozenset({
    EstadoCalibracao.EM_EXECUCAO,
    EstadoCalibracao.EM_REVISAO_1,
})

_MIN_CHARS_DOC_AGREGACAO = 50
# INV-CAL-INC-003 + NIT-DICLA-030 §7.4 — Tipo A exige n>=6 (CHECK PG
# ck_componente_tipo_a_n_min). Espelha a constraint da migration 0006.
_MIN_N_AMOSTRAS_TIPO_A = 6


class CalibracaoEstadoNaoPermiteCalcular(Exception):
    """Calibracao em estado que nao permite calcular orcamento."""


@dataclass(frozen=True, slots=True)
class ComponenteParaCalculo:
    """Componente de entrada do orcamento — matematica GUM + proveniencia §16.6.

    Une o que o MOTOR consome (u_i, tipo, grau_liberdade) com a proveniencia
    metrologica que o REGISTRO persistido exige NOT NULL (NIT-DICLA-030 §16.6:
    tipo_origem_componente, distribuicao, divisor, formula_calculo) + os campos
    do CHECK Tipo A (s_x + n_amostras >= 6).

    GATE-CAL-DOMAIN-MODEL-DRIFT (2026-05-28): antes o use case construia
    `ComponenteEntrada` (so matematica) e gravava snapshot SEM proveniencia +
    `s_x=None` sempre — o que so passava com FakeRepository; persistir no PG
    real violaria NOT NULL/CHECK. Este tipo carrega a verdade completa do
    componente. O motor permanece puro: `para_entrada_motor()` projeta so a
    matematica.

    Convencoes por tipo:
    - Tipo A (estatistico): `s_x` NOT NULL, `n_amostras` >= 6;
      `grau_liberdade` derivado de n-1 quando omitido.
    - Tipo B (outros meios): `u_i` declarado direto; `grau_liberdade` declarado
      ou None (infinito); `s_x`/`n_amostras` ausentes.
    """

    nome: str
    tipo: str  # 'A' ou 'B'
    u_i: Decimal  # incerteza-padrao do componente (entra direto no motor)
    grau_liberdade: int | None  # None = infinito (so Tipo B)
    tipo_origem_componente: TipoOrigemComponente
    distribuicao: DistribuicaoIncerteza
    divisor: Decimal  # converte meia-largura `a` em u_i (>0)
    formula_calculo: FormulaCalculoComponente
    s_x: Decimal | None = None  # Tipo A: NOT NULL (desvio-padrao amostral)
    n_amostras: int | None = None  # Tipo A: NOT NULL e >=6 (INV-CAL-INC-003)
    correlacao_com_componente_id: UUID | None = None
    coeficiente_correlacao: Decimal | None = None
    fonte_default_padrao_id: UUID | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.u_i, Decimal):
            raise TypeError(
                f"ComponenteParaCalculo.u_i deve ser Decimal "
                f"(achou {type(self.u_i).__name__}) — INV-CAL-INC-003"
            )
        if self.u_i < 0:
            raise ValueError(f"ComponenteParaCalculo.u_i < 0: {self.u_i}")
        if self.tipo not in ("A", "B"):
            raise ValueError(f"ComponenteParaCalculo.tipo invalido: {self.tipo!r}")
        if not isinstance(self.divisor, Decimal):
            raise TypeError(
                f"ComponenteParaCalculo.divisor deve ser Decimal "
                f"(achou {type(self.divisor).__name__})"
            )
        if self.divisor <= 0:
            raise ValueError(
                f"ComponenteParaCalculo.divisor deve ser > 0 (achou {self.divisor})"
            )
        if self.tipo == "A":
            if self.s_x is None:
                raise ValueError(
                    "ComponenteParaCalculo Tipo A exige s_x NOT NULL "
                    "(CHECK ck_componente_tipo_a_n_min + INV-CAL-INC-003)"
                )
            if not isinstance(self.s_x, Decimal):
                raise TypeError(
                    f"ComponenteParaCalculo.s_x deve ser Decimal "
                    f"(achou {type(self.s_x).__name__})"
                )
            if self.n_amostras is None or self.n_amostras < _MIN_N_AMOSTRAS_TIPO_A:
                raise ValueError(
                    f"ComponenteParaCalculo Tipo A exige n_amostras >= "
                    f"{_MIN_N_AMOSTRAS_TIPO_A} (NIT-DICLA-030 §7.4 + "
                    f"INV-CAL-INC-003); achou {self.n_amostras}"
                )
            # grau_liberdade derivado de n-1 quando omitido (consistencia GUM).
            if self.grau_liberdade is None:
                object.__setattr__(self, "grau_liberdade", self.n_amostras - 1)
        if self.grau_liberdade is not None and self.grau_liberdade < 1:
            raise ValueError(
                f"ComponenteParaCalculo.grau_liberdade < 1: {self.grau_liberdade}"
            )
        # INV-CAL-INC-004 — correlacao declarada exige coeficiente.
        if (
            self.correlacao_com_componente_id is not None
            and self.coeficiente_correlacao is None
        ):
            raise ValueError(
                "ComponenteParaCalculo: correlacao_com_componente_id NOT NULL "
                "exige coeficiente_correlacao (INV-CAL-INC-004)"
            )

    def para_entrada_motor(self) -> ComponenteEntrada:
        """Projeta SO a matematica que o motor GUM consome (mantem motor puro)."""
        return ComponenteEntrada(
            nome=self.nome,
            u_i=self.u_i,
            tipo=self.tipo,
            grau_liberdade=self.grau_liberdade,
        )


@dataclass(frozen=True, slots=True)
class CalcularOrcamentoIncertezaInput:
    """Payload de calculo de orcamento de incerteza."""

    calibracao_id: UUID
    componentes: tuple[ComponenteParaCalculo, ...]
    correlacoes: tuple[tuple[str, str, Decimal], ...]  # ((nome_i, nome_j, rho),...)
    versao_motor_calculo: str  # semver + commit-hash (ADR-0025)
    documentacao_agregacao: str  # >=50 chars (INV-CAL-INC-001)
    bias_orcado: Decimal | None
    bias_origem: str  # vazio se sem bias
    calculado_em: datetime  # UTC-aware
    correlation_id: UUID

    def __post_init__(self) -> None:
        if not self.componentes:
            raise ValueError(
                "calcular_orcamento_incerteza: componentes vazio (GUM cl. 5.1.2 exige >=1)"
            )
        if len(self.documentacao_agregacao) < _MIN_CHARS_DOC_AGREGACAO:
            raise ValueError(
                f"calcular_orcamento_incerteza: documentacao_agregacao precisa "
                f">= {_MIN_CHARS_DOC_AGREGACAO} chars (INV-CAL-INC-001); "
                f"achou {len(self.documentacao_agregacao)}"
            )
        if not self.versao_motor_calculo:
            raise ValueError(
                "calcular_orcamento_incerteza: versao_motor_calculo obrigatorio "
                "(INV-CAL-VERSAO-001 + ADR-0025)"
            )
        if self.calculado_em.tzinfo is None:
            raise ValueError(
                "calcular_orcamento_incerteza: calculado_em exige datetime tz-aware "
                "(INV-VIG-004)"
            )
        if self.bias_orcado is not None and not isinstance(self.bias_orcado, Decimal):
            raise TypeError(
                f"calcular_orcamento_incerteza: bias_orcado deve ser Decimal "
                f"(achou {type(self.bias_orcado).__name__}) — INV-CAL-INC-003"
            )


@dataclass(frozen=True, slots=True)
class CalcularOrcamentoIncertezaOutput:
    orcamento: OrcamentoIncertezaSnapshot
    componentes_persistidos: tuple[ComponenteIncertezaSnapshot, ...]


def _gerar_replay_hash(
    componentes: list[ComponenteEntrada],
    correlacoes: tuple[tuple[str, str, Decimal], ...],
    versao_motor: str,
    u_combinada: Decimal,
    U_expandida_arredondada: Decimal,  # - U canonico
    k: Decimal,
    dof_efetivo: int | None,
) -> str:
    """Gera HashVersionado dos inputs+outputs canonicalizados.

    Placeholder: usa SHA-256 (nao HMAC com chave KMS) — quando
    infrastructure/calibracao/hash_kms.py existir, substituir SHA-256 por
    hmac.new(chave_kms_v<NN>, bytes, sha256).digest().

    Determinismo garantido por canonicalizar_payload_para_hmac
    (sort_keys + separators sem espaco + NFC + UTF-8 sem BOM).
    """
    payload = {
        "versao_motor": versao_motor,
        "componentes": [
            {
                "nome": c.nome,
                "u_i": str(c.u_i),
                "tipo": c.tipo,
                "dof": c.grau_liberdade,
            }
            for c in componentes
        ],
        "correlacoes": [
            {"i": rho_ij[0], "j": rho_ij[1], "rho": str(rho_ij[2])}
            for rho_ij in correlacoes
        ],
        "outputs": {
            "u_combinada": str(u_combinada),
            "U_expandida": str(U_expandida_arredondada),
            "k": str(k),
            "dof_efetivo": dof_efetivo,
        },
    }
    bytes_canon = canonicalizar_payload_para_hmac(payload)
    digest = hashlib.sha256(bytes_canon).digest()
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, digest)


def executar(
    inp: CalcularOrcamentoIncertezaInput,
    calibracao_repo: CalibracaoRepository,
    orcamento_repo: OrcamentoIncertezaRepository,
) -> CalcularOrcamentoIncertezaOutput:
    """Calcula orcamento de incerteza + persiste atomicamente."""
    calibracao = calibracao_repo.obter_por_id(inp.calibracao_id)
    if calibracao is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if calibracao.status not in _ESTADOS_CALCULO_PERMITIDO:
        raise CalibracaoEstadoNaoPermiteCalcular(
            f"status atual={calibracao.status.value}; calcular_orcamento_incerteza "
            f"exige status IN "
            f"{sorted(s.value for s in _ESTADOS_CALCULO_PERMITIDO)}"
        )

    # ---- Algoritmo 1 (GUM Decimal puro) ----
    # Projeta SO a matematica pro motor (proveniencia §16.6 nao afeta o calculo,
    # so o registro persistido). Motor permanece puro (ComponenteEntrada).
    entradas_motor = [c.para_entrada_motor() for c in inp.componentes]
    resultado_gum = propagar(
        entradas_motor,
        list(inp.correlacoes) if inp.correlacoes else None,
    )

    # NIT-DICLA-030 §7.5 — arredonda U_expandida pra 2 sig
    U_arredondada = arredondar_2_digitos_significativos(  # - U canonico
        resultado_gum.U_expandida
    )

    # Replay hash deterministico (ADR-0025 cl. 7.11) — calculado SO sobre os
    # inputs matematicos (u_i/tipo/dof/correlacoes/versao). Proveniencia §16.6
    # nao entra no hash (nao afeta o resultado do calculo).
    replay_hash = _gerar_replay_hash(
        entradas_motor,
        inp.correlacoes,
        inp.versao_motor_calculo,
        resultado_gum.u_combinada,
        U_arredondada,
        resultado_gum.fator_k,
        resultado_gum.grau_liberdade_efetivo,
    )

    # Algoritmo 1 resultado completo (vai pra JSONB algoritmo_1_resultado)
    algoritmo_1_resultado: dict[str, object] = {
        "u_combinada": str(resultado_gum.u_combinada),
        "U_expandida_bruta": str(resultado_gum.U_expandida),
        "U_expandida_arredondada": str(U_arredondada),
        "k": str(resultado_gum.fator_k),
        "grau_liberdade_efetivo": resultado_gum.grau_liberdade_efetivo,
        "nivel_confianca": str(resultado_gum.nivel_confianca),
        "n_componentes": len(inp.componentes),
        "n_correlacoes": len(inp.correlacoes),
    }

    orcamento_id = uuid4()
    # Welch-Satterthwaite pode retornar None (todos componentes Tipo B
    # com dof=infinito). Para o snapshot persistido, mapeamos None pra
    # Decimal grande (999999) como marcador de "infinito praticamente".
    dof_persistido = (
        Decimal(resultado_gum.grau_liberdade_efetivo)
        if resultado_gum.grau_liberdade_efetivo is not None
        else Decimal("999999")
    )

    orcamento = OrcamentoIncertezaSnapshot(
        id=orcamento_id,
        tenant_id=calibracao.tenant_id,
        calibracao_id=inp.calibracao_id,
        u_combinada=resultado_gum.u_combinada,
        grau_liberdade_efetivo=dof_persistido,
        k=resultado_gum.fator_k,
        U_expandida=U_arredondada,
        nivel_confianca=resultado_gum.nivel_confianca,
        documentacao_agregacao=inp.documentacao_agregacao,
        versao_motor_calculo=inp.versao_motor_calculo,
        algoritmo_1_resultado=algoritmo_1_resultado,
        # Monte Carlo BLOQUEADO DEP-001 numpy — algoritmo_2 NULL ate
        # numpy entrar via auditor-supplychain review.
        algoritmo_2_resultado=None,
        divergencia_pct=None,
        replay_determinismo_hash=replay_hash,
        bias_orcado=inp.bias_orcado,
        bias_origem=inp.bias_origem,
        arredondamento_aplicado_regra=REGRA_ID,
        calculado_em=inp.calculado_em,
        correlation_id=inp.correlation_id,
    )

    # Componentes persistidos (1:N) — agora com proveniencia §16.6 completa
    # (GATE-CAL-DOMAIN-MODEL-DRIFT). s_x/n_amostras vem do proprio componente
    # (Tipo A validado em ComponenteParaCalculo.__post_init__ — n>=6 + s_x).
    componentes_persistidos: list[ComponenteIncertezaSnapshot] = []
    for comp in inp.componentes:
        u_i_quad = comp.u_i * comp.u_i  # u_i^2 = contribuicao base
        componentes_persistidos.append(
            ComponenteIncertezaSnapshot(
                id=uuid4(),
                tenant_id=calibracao.tenant_id,
                orcamento_incerteza_id=orcamento_id,
                nome_componente=comp.nome,
                tipo_componente=comp.tipo,
                tipo_origem_componente=comp.tipo_origem_componente,
                distribuicao=comp.distribuicao,
                divisor=comp.divisor,
                formula_calculo=comp.formula_calculo,
                valor_estimativa=comp.u_i,
                contribuicao=u_i_quad,
                grau_liberdade=(
                    Decimal(comp.grau_liberdade)
                    if comp.grau_liberdade is not None
                    else None
                ),
                n_amostras=comp.n_amostras,
                s_x=comp.s_x,
                correlacao_com_componente_id=comp.correlacao_com_componente_id,
                coeficiente_correlacao=comp.coeficiente_correlacao,
                fonte_default_padrao_id=comp.fonte_default_padrao_id,
            )
        )

    orcamento_repo.salvar_orcamento_com_componentes(
        orcamento, componentes_persistidos
    )

    return CalcularOrcamentoIncertezaOutput(
        orcamento=orcamento,
        componentes_persistidos=tuple(componentes_persistidos),
    )
