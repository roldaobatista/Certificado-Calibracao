"""Derivação de incerteza Tipo A POR PONTO — ADR-0077 (SAN-INCERTEZA-PONTO).

Puro (Decimal, sem Django/PG). O motor GUM (`gum_classico`) permanece intacto: este
módulo só PREPARA o componente Tipo A de cada ponto (s_x das repetições daquele ponto)
aplicando a regra n>=6 perfil-aware do consultor-rbc (Q-RBC-2), e agrega o pior-caso.

Regras cravadas (consultor-rbc 2026-05-31, base GUM/NIT-DICLA-030 §7.4/EA-4/02 §3.2):
- n >= 6  -> s_x do próprio ponto (SX_PROPRIO), dof = n-1.
- 2 <= n < 6 -> usa s_pooled (validação do método) se houver (S_POOLED, dof do pool);
  senão: perfil A = FAIL-CLOSED (TipoAInsuficienteError); B/C/D = ressalva registrada
  (SX_PROPRIO + tipo_a_insuficiente=True).
- n < 2 -> sem Tipo A no ponto (AUSENTE) — só Tipo B; registrado, nunca silencioso.

Agregado de "visão geral" = PIOR CASO (max U entre pontos), NÃO média (Q-RBC-3 — média
de incertezas subestima). Rótulo no consumidor: "U máxima na faixa".
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.domain.metrologia.calibracao.enums import MetodoTipoAPonto

# NIT-DICLA-030 §7.4 — Tipo A por repetibilidade do próprio ponto exige n >= 6.
N_MINIMO_TIPO_A = 6
_PERFIL_ACREDITADO = "A"


class TipoAInsuficienteError(Exception):
    """Perfil A: ponto com 2 <= n < 6 e SEM s_pooled válido — fail-closed.

    Emitir RBC com Tipo A insuficiente (n<6 sem desvio combinado) é NC de
    supervisão CGCRE (NIT-DICLA-030 §7.4). B/C/D não levanta (ressalva registrada).
    """

    def __init__(self, ponto: Decimal, n: int) -> None:
        self.ponto = ponto
        self.n = n
        super().__init__(
            f"TipoAInsuficiente ponto={ponto} n={n} (<{N_MINIMO_TIPO_A}) sem s_pooled — "
            f"perfil A fail-closed (NIT-DICLA-030 §7.4)"
        )


@dataclass(frozen=True, slots=True)
class ResultadoTipoAPonto:
    """Componente Tipo A resolvido para UM ponto (probatório cl. 7.5/7.11)."""

    metodo: MetodoTipoAPonto
    s_usado: Decimal | None  # None quando AUSENTE
    n_repeticoes: int
    dof: int | None  # graus de liberdade do Tipo A; None quando AUSENTE
    tipo_a_insuficiente: bool  # ressalva B/C/D (2<=n<6 sem pool)


def desvio_padrao_amostral(valores: list[Decimal]) -> Decimal:
    """s_x experimental (GUM cl. 4.2.2): sqrt( Σ(x-x̄)² / (n-1) ). Exige n >= 2."""
    n = len(valores)
    if n < 2:
        raise ValueError(f"desvio_padrao_amostral: n < 2 ({n})")
    soma = sum(valores, Decimal(0))
    media = soma / Decimal(n)
    var = sum(((x - media) * (x - media) for x in valores), Decimal(0)) / Decimal(n - 1)
    if var < 0:  # defesa numérica (não deveria ocorrer)
        var = Decimal(0)
    return var.sqrt()


def derivar_tipo_a_ponto(
    *,
    valores_repeticoes: list[Decimal],
    perfil: str,
    s_pooled: tuple[Decimal, int] | None = None,
) -> ResultadoTipoAPonto:
    """Resolve o Tipo A de UM ponto aplicando a regra n>=6 perfil-aware (Q-RBC-2).

    `s_pooled = (s, dof)` — desvio-padrão combinado validado do método (opcional).
    """
    n = len(valores_repeticoes)
    perfil_norm = perfil.strip().upper()

    if n < 2:
        # n < 2: impossível s_x — sem Tipo A no ponto (registrado).
        return ResultadoTipoAPonto(
            metodo=MetodoTipoAPonto.AUSENTE,
            s_usado=None,
            n_repeticoes=n,
            dof=None,
            tipo_a_insuficiente=True,
        )

    if n >= N_MINIMO_TIPO_A:
        s_x = desvio_padrao_amostral(valores_repeticoes)
        return ResultadoTipoAPonto(
            metodo=MetodoTipoAPonto.SX_PROPRIO,
            s_usado=s_x,
            n_repeticoes=n,
            dof=n - 1,
            tipo_a_insuficiente=False,
        )

    # 2 <= n < 6 — insuficiente para s_x do próprio ponto.
    if s_pooled is not None:
        s_pool, dof_pool = s_pooled
        if s_pool < 0:
            raise ValueError(f"derivar_tipo_a_ponto: s_pooled < 0 ({s_pool})")
        return ResultadoTipoAPonto(
            metodo=MetodoTipoAPonto.S_POOLED,
            s_usado=s_pool,
            n_repeticoes=n,
            dof=dof_pool,
            tipo_a_insuficiente=False,
        )

    if perfil_norm == _PERFIL_ACREDITADO:
        raise TipoAInsuficienteError(Decimal(0), n)

    # B/C/D — ressalva registrada: usa s_x do próprio ponto (n<6), flag insuficiente.
    s_x = desvio_padrao_amostral(valores_repeticoes)
    return ResultadoTipoAPonto(
        metodo=MetodoTipoAPonto.SX_PROPRIO,
        s_usado=s_x,
        n_repeticoes=n,
        dof=n - 1,
        tipo_a_insuficiente=True,
    )


def agregado_pior_caso(u_expandida_por_ponto: list[Decimal]) -> Decimal:
    """Agregado NÃO-NORMATIVO de "visão geral" = max U entre pontos (Q-RBC-3).

    Média aritmética é proibida (subestima). Rótulo no consumidor: "U máxima na
    faixa" — nunca "U da calibração"/"U média"; não usar para conformidade de ponto.
    """
    if not u_expandida_por_ponto:
        raise ValueError("agregado_pior_caso: lista de pontos vazia")
    return max(u_expandida_por_ponto)
