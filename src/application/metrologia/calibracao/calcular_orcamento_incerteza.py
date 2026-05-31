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
    CalibracaoSnapshot,
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
    ResultadoGUM,
    propagar,
)
from src.domain.metrologia.calibracao.motor_calculo.incerteza_por_ponto import (
    derivar_tipo_a_ponto,
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
# Perfil acreditado (RBC) — unico que sofre fail-closed no caminho por-ponto.
_PERFIL_ACREDITADO = "A"
# Nome canonico do componente Tipo A derivado por ponto (repetibilidade). Nao
# persiste como ComponenteIncerteza global no modo por-ponto (decisao tech-lead
# opcao (a)); serve so para o motor GUM montar a combinacao do ponto.
_NOME_COMPONENTE_TIPO_A = "repetibilidade"


class CalibracaoEstadoNaoPermiteCalcular(Exception):
    """Calibracao em estado que nao permite calcular orcamento."""


class EscalonamentoNaoSuportadoError(Exception):
    """Perfil A: componente Tipo B com lei != CONSTANTE na 1a fatia (Q-FIS-3).

    Tratar como constante um componente que escala com o mensurando (incerteza do
    padrao a+b·X com b!=0, deriva proporcional) subestima U nos pontos altos da
    faixa = NC de supervisao CGCRE (NIT-DICLA-030 §7.4 + ILAC-P14 §5). A 2a fatia
    (escalonamento) habilita PROPORCIONAL/LINEAR_AFIM. B/C/D registra ressalva e
    nao levanta (capacidade interna nao-acreditada).
    """

    def __init__(self, nome_componente: str, lei: LeiEscalonamento) -> None:
        self.nome_componente = nome_componente
        self.lei = lei
        super().__init__(
            f"EscalonamentoNaoSuportado componente={nome_componente!r} "
            f"lei={lei.value} — 1a fatia RBC so admite CONSTANTE (Q-FIS-3)"
        )


@dataclass(frozen=True, slots=True)
class PontoParaCalculo:
    """Um ponto de calibracao com suas repeticoes — deriva Tipo A (ADR-0077).

    `valores_repeticoes` = leituras do ponto (deriva s_x via desvio_padrao_amostral
    quando n>=6; senao s_pooled). `s_pooled = (s, dof)` = desvio combinado validado
    do metodo (GUM §4.2.4) quando 2<=n<6 ou indicacao unica n=1.
    """

    ponto_calibracao: Decimal
    valores_repeticoes: tuple[Decimal, ...]
    s_pooled: tuple[Decimal, int] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.ponto_calibracao, Decimal):
            raise TypeError(
                f"PontoParaCalculo.ponto_calibracao deve ser Decimal "
                f"(achou {type(self.ponto_calibracao).__name__})"
            )
        for v in self.valores_repeticoes:
            if not isinstance(v, Decimal):
                raise TypeError(
                    "PontoParaCalculo.valores_repeticoes: todos os valores devem "
                    f"ser Decimal (achou {type(v).__name__})"
                )
        if self.s_pooled is not None:
            s_pool, dof_pool = self.s_pooled
            if not isinstance(s_pool, Decimal):
                raise TypeError(
                    f"PontoParaCalculo.s_pooled[0] deve ser Decimal "
                    f"(achou {type(s_pool).__name__})"
                )
            if dof_pool < 1:
                raise ValueError(
                    f"PontoParaCalculo.s_pooled[1] (dof) deve ser >= 1 "
                    f"(achou {dof_pool})"
                )


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
    # ADR-0077 Q-RBC-1: lei de variacao do componente Tipo B na faixa. 1a fatia so
    # admite CONSTANTE em RBC (portao fail-closed no use case por-ponto). Default
    # CONSTANTE mantem o path flat inalterado.
    lei_escalonamento: LeiEscalonamento = LeiEscalonamento.CONSTANTE

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
    # ADR-0077 — modo por-ponto. Vazio (default) = path flat legado INTACTO.
    # Quando nao-vazio: `componentes` carrega SO os Tipo B base (CONSTANTE); o
    # Tipo A e derivado por ponto das `valores_repeticoes`. `perfil_tenant`
    # obrigatorio (regra n<6 / AUSENTE fail-closed perfil A — Q-RBC-2/Q-FIS-4).
    pontos: tuple[PontoParaCalculo, ...] = ()
    perfil_tenant: str = ""

    def __post_init__(self) -> None:
        if not self.componentes:
            raise ValueError(
                "calcular_orcamento_incerteza: componentes vazio (GUM cl. 5.1.2 exige >=1)"
            )
        if self.pontos:
            # Modo por-ponto: perfil obrigatorio (fail-closed sem perfil declarado)
            # e `componentes` so Tipo B (Tipo A vem derivado das repeticoes).
            if not self.perfil_tenant:
                raise ValueError(
                    "calcular_orcamento_incerteza: modo por-ponto exige "
                    "perfil_tenant (regra n<6 fail-closed — ADR-0077 Q-RBC-2)"
                )
            tipos_a = [c.nome for c in self.componentes if c.tipo == "A"]
            if tipos_a:
                raise ValueError(
                    "calcular_orcamento_incerteza: modo por-ponto exige "
                    "`componentes` so Tipo B (o Tipo A e derivado por ponto das "
                    f"repeticoes); achou Tipo A: {tipos_a}"
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
    # ADR-0077 — N orcamentos por ponto (vazio no path flat).
    pontos: tuple[OrcamentoPorPontoSnapshot, ...] = ()


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

    # ADR-0077 — modo por-ponto (aditivo; path flat abaixo intacto).
    if inp.pontos:
        return _executar_por_ponto(inp, calibracao, orcamento_repo)

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
    componentes_persistidos = [
        _snapshot_componente(comp, calibracao.tenant_id, orcamento_id)
        for comp in inp.componentes
    ]

    orcamento_repo.salvar_orcamento_com_componentes(
        orcamento, componentes_persistidos
    )

    return CalcularOrcamentoIncertezaOutput(
        orcamento=orcamento,
        componentes_persistidos=tuple(componentes_persistidos),
    )


def _snapshot_componente(
    comp: ComponenteParaCalculo,
    tenant_id: UUID,
    orcamento_id: UUID,
) -> ComponenteIncertezaSnapshot:
    """Projeta um ComponenteParaCalculo no snapshot persistido (1:N do orcamento).

    Usado pelo path flat (todos os componentes) e pelo path por-ponto (SO os Tipo B
    base — decisao tech-lead opcao (a): o Tipo A nao vira ComponenteIncerteza global
    no modo por-ponto, preservando o CHECK ck_componente_tipo_a_n_min).
    """
    u_i_quad = comp.u_i * comp.u_i  # u_i^2 = contribuicao base
    return ComponenteIncertezaSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
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
            Decimal(comp.grau_liberdade) if comp.grau_liberdade is not None else None
        ),
        n_amostras=comp.n_amostras,
        s_x=comp.s_x,
        correlacao_com_componente_id=comp.correlacao_com_componente_id,
        coeficiente_correlacao=comp.coeficiente_correlacao,
        fonte_default_padrao_id=comp.fonte_default_padrao_id,
    )


@dataclass(frozen=True, slots=True)
class _PontoCalc:
    """Resultado intermediario de um ponto (interno ao use case por-ponto)."""

    snap: OrcamentoPorPontoSnapshot
    gum: ResultadoGUM
    U_arred: Decimal  # - U arredondada NIT-DICLA-030 §7.5
    replay_hash: str
    ponto: Decimal


def _calcular_ponto(
    ponto: PontoParaCalculo,
    *,
    perfil: str,
    entradas_b: list[ComponenteEntrada],
    correlacoes: tuple[tuple[str, str, Decimal], ...],
    versao_motor: str,
    lei_aplicada: LeiEscalonamento,
    tenant_id: UUID,
    orcamento_id: UUID,
) -> _PontoCalc:
    """Deriva Tipo A do ponto + combina com Tipo B base + propaga GUM (1 chamada).

    Perfil A pode levantar TipoAInsuficienteError/TipoAAusenteError (Q-FIS-2/4) —
    propaga para o caller abortar atomicamente (nenhum ponto persistido).
    """
    resultado_a = derivar_tipo_a_ponto(
        valores_repeticoes=list(ponto.valores_repeticoes),
        perfil=perfil,
        s_pooled=ponto.s_pooled,
    )
    entradas: list[ComponenteEntrada] = []
    s_aplicado: Decimal | None = None
    if resultado_a.metodo is not MetodoTipoAPonto.AUSENTE:
        s_aplicado = resultado_a.s_usado
        if s_aplicado is None:  # defesa — dominio garante s_usado quando != AUSENTE
            raise ValueError(
                "derivar_tipo_a_ponto: metodo != AUSENTE com s_usado None"
            )
        # u_A = s_usado/√n (incerteza-padrao da MEDIA de n repeticoes; Q-FIS-1).
        u_a = s_aplicado / Decimal(resultado_a.n_repeticoes).sqrt()
        entradas.append(
            ComponenteEntrada(
                nome=_NOME_COMPONENTE_TIPO_A,
                u_i=u_a,
                tipo="A",
                grau_liberdade=resultado_a.dof,
            )
        )
    entradas.extend(entradas_b)

    resultado_gum = propagar(entradas, list(correlacoes) if correlacoes else None)
    U_arred = arredondar_2_digitos_significativos(resultado_gum.U_expandida)
    replay_hash = _gerar_replay_hash(
        entradas,
        correlacoes,
        versao_motor,
        resultado_gum.u_combinada,
        U_arred,
        resultado_gum.fator_k,
        resultado_gum.grau_liberdade_efetivo,
    )
    dof_ponto = (
        Decimal(resultado_gum.grau_liberdade_efetivo)
        if resultado_gum.grau_liberdade_efetivo is not None
        else Decimal("999999")
    )
    snap = OrcamentoPorPontoSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
        orcamento_incerteza_id=orcamento_id,
        ponto_calibracao=ponto.ponto_calibracao,
        u_combinada_no_ponto=resultado_gum.u_combinada,
        U_expandida_no_ponto=U_arred,
        k_no_ponto=resultado_gum.fator_k,
        nivel_confianca_no_ponto=resultado_gum.nivel_confianca,
        grau_liberdade_efetivo_no_ponto=dof_ponto,
        replay_determinismo_hash_no_ponto=replay_hash,
        metodo_tipo_a_ponto=resultado_a.metodo,
        n_repeticoes_ponto=resultado_a.n_repeticoes,
        lei_escalonamento_aplicada=lei_aplicada,
        tipo_a_insuficiente=resultado_a.tipo_a_insuficiente,
        s_tipo_a_no_ponto=s_aplicado,
    )
    return _PontoCalc(
        snap=snap,
        gum=resultado_gum,
        U_arred=U_arred,
        replay_hash=replay_hash,
        ponto=ponto.ponto_calibracao,
    )


def _executar_por_ponto(
    inp: CalcularOrcamentoIncertezaInput,
    calibracao: CalibracaoSnapshot,
    orcamento_repo: OrcamentoIncertezaRepository,
) -> CalcularOrcamentoIncertezaOutput:
    """Caminho por-ponto (ADR-0077). Produz N OrcamentoPorPonto + agregado pior-caso.

    Decisoes cravadas (tech-lead + consultor-rbc 2026-05-31):
    - Tipo A derivado por ponto das repeticoes; u_A = s_usado/√n (Q-FIS-1);
      motor GUM roda 1x por ponto (N chamadas a propagar()).
    - Tipo B base CONSTANTE (1a fatia); portao fail-closed perfil A se lei != CONSTANTE
      (Q-FIS-3), avaliado ANTES do loop (propriedade do orcamento, nao do ponto) —
      atomico: nenhum ponto e emitido.
    - Agregado global = ponto de PIOR CASO (max U, "U maxima na faixa", nao-normativo);
      ComponenteIncerteza 1:N global = SO os Tipo B (opcao (a) — preserva CHECK n>=6).
    - replay_determinismo_hash global = hash do ponto j* (coincide por construcao);
      cadeia_pontos_hash = fecho encadeando os hashes por ponto em ordem ASC.
    """
    perfil = inp.perfil_tenant.strip().upper()
    tipo_b_base = list(inp.componentes)  # __post_init__ garantiu: todos Tipo B

    # --- Portao escalonamento (Q-FIS-3) — antes do loop, atomico. ---
    nao_constantes = [
        c for c in tipo_b_base
        if c.lei_escalonamento is not LeiEscalonamento.CONSTANTE
    ]
    if nao_constantes and perfil == _PERFIL_ACREDITADO:
        c0 = nao_constantes[0]
        raise EscalonamentoNaoSuportadoError(c0.nome, c0.lei_escalonamento)
    # B/C/D com lei declarada nao-constante: rastro de ressalva (2a fatia pendente).
    lei_aplicada = (
        nao_constantes[0].lei_escalonamento
        if nao_constantes
        else LeiEscalonamento.CONSTANTE
    )

    orcamento_id = uuid4()
    entradas_b = [c.para_entrada_motor() for c in tipo_b_base]

    pontos_calc = [
        _calcular_ponto(
            ponto,
            perfil=perfil,
            entradas_b=entradas_b,
            correlacoes=inp.correlacoes,
            versao_motor=inp.versao_motor_calculo,
            lei_aplicada=lei_aplicada,
            tenant_id=calibracao.tenant_id,
            orcamento_id=orcamento_id,
        )
        for ponto in inp.pontos
    ]

    # j* = pior caso (max U). Empate -> menor ponto_calibracao (determinismo total,
    # independe da ordem de chegada das leituras).
    vencedor = max(pontos_calc, key=lambda pc: (pc.U_arred, -pc.ponto))
    gum_j = vencedor.gum
    dof_persistido = (
        Decimal(gum_j.grau_liberdade_efetivo)
        if gum_j.grau_liberdade_efetivo is not None
        else Decimal("999999")
    )
    n_comp_j = len(tipo_b_base) + (
        0 if vencedor.snap.metodo_tipo_a_ponto is MetodoTipoAPonto.AUSENTE else 1
    )
    algoritmo_1_resultado: dict[str, object] = {
        "u_combinada": str(gum_j.u_combinada),
        "U_expandida_bruta": str(gum_j.U_expandida),
        "U_expandida_arredondada": str(vencedor.U_arred),
        "k": str(gum_j.fator_k),
        "grau_liberdade_efetivo": gum_j.grau_liberdade_efetivo,
        "nivel_confianca": str(gum_j.nivel_confianca),
        "n_componentes": n_comp_j,
        "n_correlacoes": len(inp.correlacoes),
        "modo": "por_ponto",
        "n_pontos": len(pontos_calc),
        "ponto_pior_caso": str(vencedor.ponto),
    }

    # Cadeia de fecho — encadeia os hashes por ponto em ordem ponto_calibracao ASC.
    ordenados = sorted(pontos_calc, key=lambda pc: pc.ponto)
    cadeia_payload = {
        "versao_motor": inp.versao_motor_calculo,
        "pontos": [
            {"ponto": str(pc.ponto), "hash": pc.replay_hash} for pc in ordenados
        ],
    }
    cadeia_hash = formatar_hash_versionado(
        VERSAO_HMAC_ATUAL,
        hashlib.sha256(canonicalizar_payload_para_hmac(cadeia_payload)).digest(),
    )

    orcamento = OrcamentoIncertezaSnapshot(
        id=orcamento_id,
        tenant_id=calibracao.tenant_id,
        calibracao_id=inp.calibracao_id,
        u_combinada=gum_j.u_combinada,
        grau_liberdade_efetivo=dof_persistido,
        k=gum_j.fator_k,
        U_expandida=vencedor.U_arred,
        nivel_confianca=gum_j.nivel_confianca,
        documentacao_agregacao=inp.documentacao_agregacao,
        versao_motor_calculo=inp.versao_motor_calculo,
        algoritmo_1_resultado=algoritmo_1_resultado,
        algoritmo_2_resultado=None,
        divergencia_pct=None,
        # = hash do ponto j* por construcao (Q4 tech-lead); cadeia em campo proprio.
        replay_determinismo_hash=vencedor.replay_hash,
        bias_orcado=inp.bias_orcado,
        bias_origem=inp.bias_origem,
        arredondamento_aplicado_regra=REGRA_ID,
        calculado_em=inp.calculado_em,
        correlation_id=inp.correlation_id,
        cadeia_pontos_hash=cadeia_hash,
    )

    # Global persiste SO os Tipo B (decisao tech-lead opcao (a)) — preserva o CHECK
    # ck_componente_tipo_a_n_min. O Tipo A vive em OrcamentoPorPonto[j*].
    componentes_persistidos = [
        _snapshot_componente(c, calibracao.tenant_id, orcamento_id)
        for c in tipo_b_base
    ]
    pontos_snap = tuple(pc.snap for pc in pontos_calc)

    orcamento_repo.salvar_orcamento_com_componentes(
        orcamento, componentes_persistidos, pontos_snap
    )

    return CalcularOrcamentoIncertezaOutput(
        orcamento=orcamento,
        componentes_persistidos=tuple(componentes_persistidos),
        pontos=pontos_snap,
    )
