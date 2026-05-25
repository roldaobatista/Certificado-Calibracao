# ruff: noqa: RUF001, RUF002, RUF003 — simbolos gregos canonicos GUM (ν, ρ) na notacao metrologica oficial
"""GUM classico — propagacao de incerteza Decimal puro (P4 Fase 3 Batch B — T-CAL-050..054).

JCGM 100:2008 (GUM) + NIT-DICLA-030 rev. 15.

Por que Decimal e nao float:
- ISO 17025 cl. 7.6 + INV-CAL-INC-003 exigem ausencia de erro de
  arredondamento metrologico em chain de calculo. Float double-precision
  acumula erro em 1e-16 por operacao; em 1000 operacoes, perde-se
  precisao relevante pra grandezas com 6+ digitos.
- Replay deterministico (ADR-0025 cl. 7.11): mesmo input -> mesmo output,
  sempre, em qualquer plataforma. Float introduz IEEE 754 dependente de
  hardware/compilador.

Algoritmo (GUM cl. 5):
  Tipo A: u_a = s_x / sqrt(n), grau_liberdade = n - 1
  Tipo B: u_b informado direto, grau_liberdade declarado (default infinito)
  Combinada: u_c = sqrt(soma(u_i^2)) sem correlacao
            u_c = sqrt(soma(u_i^2) + 2·soma(ρ_ij · u_i · u_j)) com correlacao
  Welch-Satterthwaite (cl. G.4):
    ν_eff = (soma(u_i^2))^2 / soma(u_i^4 / ν_i)
    Componentes com ν=infinito nao contribuem (termo zero).
  Expansao:
    U = k · u_c
    k = 2.0 quando ν_eff = infinito (95.45% cobertura normal)
    k = tabela t-Student para ν_eff finito (k_95 a partir tabela G.2 GUM).

Catalogo:
  - ComponenteEntrada: dataclass com (nome, u_i, tipo, grau_liberdade)
  - combinar_tipo_a(s_x, n) -> (u_a, dof_a)
  - combinar_componentes(componentes, correlacoes=None) -> u_c (Decimal)
  - welch_satterthwaite(componentes) -> dof_efetivo (int | None)
  - fator_k_para_95(dof) -> k (Decimal)
  - propagar(componentes, correlacoes=None) -> ResultadoGUM (combinada + expandida)

NAO incluido nesta release:
- Componentes assimetricos (distribuicao triangular nao-simetrica).
- Sensibilidades dy/dx (coeficiente parcial) — assumido 1 pra todos
  os componentes (caso simples NIT-DICLA-030; ampliacao em V2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, getcontext

# Precisao decimal pra calculos GUM. Padrao Decimal eh 28; subimos pra 50
# pra absorver acumulacao em chain longa. Configurado no escopo do modulo;
# chamador pode setar getcontext().prec maior se necessario.
_PRECISAO_GUM = 50
getcontext().prec = max(getcontext().prec, _PRECISAO_GUM)


# Tabela t-Student para 95.45% cobertura (k_95 — GUM Tabela G.2).
# Indices: grau_liberdade -> k_95.
# Valores oficiais GUM JCGM 100:2008 Tabela G.2 (coverage 95.45%).
# Acima de ν=30: usar 2.000 (proximo do normal limite).
_TABELA_K_95_45: dict[int, Decimal] = {
    1: Decimal("13.97"),
    2: Decimal("4.527"),
    3: Decimal("3.307"),
    4: Decimal("2.869"),
    5: Decimal("2.649"),
    6: Decimal("2.517"),
    7: Decimal("2.429"),
    8: Decimal("2.366"),
    9: Decimal("2.320"),
    10: Decimal("2.284"),
    11: Decimal("2.255"),
    12: Decimal("2.231"),
    13: Decimal("2.212"),
    14: Decimal("2.195"),
    15: Decimal("2.181"),
    16: Decimal("2.169"),
    17: Decimal("2.158"),
    18: Decimal("2.149"),
    19: Decimal("2.140"),
    20: Decimal("2.133"),
    25: Decimal("2.105"),
    30: Decimal("2.087"),
    40: Decimal("2.064"),
    50: Decimal("2.051"),
    100: Decimal("2.025"),
}
_K_INFINITO_95_45 = Decimal("2.000")


@dataclass(frozen=True)
class ComponenteEntrada:
    """Componente de incerteza individual (Tipo A ou Tipo B).

    Tipo A: u_i calculado a partir de s_x (desvio padrao experimental)
      e n (numero de amostras). grau_liberdade = n - 1.
    Tipo B: u_i declarado direto (calibracao padrao, especificacao
      fabricante, etc). grau_liberdade declarado ou infinito.

    Invariantes:
      - u_i >= 0 (incerteza nao-negativa)
      - tipo in {'A', 'B'}
      - grau_liberdade >= 1 ou None (None = infinito, so Tipo B)
      - Tipo A sempre tem grau_liberdade (n - 1 >= 1, exige n >= 2)
    """

    nome: str
    u_i: Decimal
    tipo: str  # 'A' ou 'B'
    grau_liberdade: int | None  # None = infinito (so Tipo B)

    def __post_init__(self) -> None:
        if not isinstance(self.u_i, Decimal):
            raise TypeError(
                f"ComponenteEntrada.u_i deve ser Decimal "
                f"(achou {type(self.u_i).__name__}) — INV-CAL-INC-003"
            )
        if self.u_i < 0:
            raise ValueError(f"ComponenteEntrada.u_i < 0: {self.u_i}")
        if self.tipo not in ("A", "B"):
            raise ValueError(f"ComponenteEntrada.tipo invalido: {self.tipo!r}")
        if self.tipo == "A" and self.grau_liberdade is None:
            raise ValueError(
                "ComponenteEntrada Tipo A exige grau_liberdade declarado "
                "(= n - 1; n >= 2 -> dof >= 1)"
            )
        if self.grau_liberdade is not None and self.grau_liberdade < 1:
            raise ValueError(
                f"ComponenteEntrada.grau_liberdade < 1: {self.grau_liberdade}"
            )


@dataclass(frozen=True)
class ResultadoGUM:
    """Resultado da propagacao GUM (incerteza padrao combinada + expandida).

    Campos:
      u_combinada: u_c (incerteza padrao combinada, Decimal).
      grau_liberdade_efetivo: ν_eff Welch-Satterthwaite (int | None).
        None = todos componentes Tipo B com dof=infinito.
      fator_k: k_95 aplicado (Decimal).
      U_expandida: U = k · u_c (sem arredondamento metrologico ainda).
      nivel_confianca: cobertura nominal (Decimal, ex: 0.9545).
    """

    u_combinada: Decimal
    grau_liberdade_efetivo: int | None
    fator_k: Decimal
    U_expandida: Decimal  # - nome metrologico canonico
    nivel_confianca: Decimal = field(default_factory=lambda: Decimal("0.9545"))


def _sqrt_decimal(x: Decimal) -> Decimal:
    """Raiz quadrada Decimal de alta precisao (Newton-Raphson).

    Decimal nao tem sqrt nativo de alta precisao; usamos `.sqrt()` do contexto.
    """
    if x < 0:
        raise ValueError(f"_sqrt_decimal: x negativo {x}")
    return x.sqrt()


def combinar_tipo_a(s_x: Decimal, n: int) -> tuple[Decimal, int]:
    """Calcula incerteza Tipo A (estatistica) — GUM cl. 4.2.

    u_a = s_x / sqrt(n)
    grau_liberdade = n - 1

    Args:
      s_x: desvio padrao experimental (Decimal).
      n: numero de amostras (>= 2; NIT-DICLA-030 §7.4 exige n >= 6 — verificacao
        em entidade ComponenteIncerteza).

    Retorna:
      (u_a, grau_liberdade) — incerteza padrao Tipo A + graus de liberdade.

    Levanta:
      ValueError — n < 2 ou s_x < 0.
    """
    if not isinstance(s_x, Decimal):
        raise TypeError(
            f"combinar_tipo_a.s_x deve ser Decimal (achou {type(s_x).__name__})"
        )
    if s_x < 0:
        raise ValueError(f"combinar_tipo_a: s_x < 0: {s_x}")
    if n < 2:
        raise ValueError(
            f"combinar_tipo_a: n < 2 ({n}) — incerteza Tipo A exige n >= 2 "
            f"(NIT-DICLA-030 §7.4 recomenda n >= 6)"
        )
    u_a = s_x / _sqrt_decimal(Decimal(n))
    return u_a, n - 1


def combinar_componentes(
    componentes: list[ComponenteEntrada],
    correlacoes: list[tuple[str, str, Decimal]] | None = None,
) -> Decimal:
    """Combina componentes de incerteza segundo GUM cl. 5.1.2 + 5.2.2.

    Sem correlacao:
      u_c^2 = soma(u_i^2)
    Com correlacao:
      u_c^2 = soma(u_i^2) + 2·soma(ρ_ij · u_i · u_j)

    Args:
      componentes: lista de ComponenteEntrada (>= 1).
      correlacoes: lista opcional de (nome_i, nome_j, ρ_ij) — coeficiente
        de correlacao (-1 <= ρ <= 1). Pares nao listados assumidos 0.

    Retorna:
      u_c (Decimal) — incerteza padrao combinada.

    Levanta:
      ValueError — lista vazia OU ρ fora de [-1, 1].
    """
    if not componentes:
        raise ValueError("combinar_componentes: lista vazia (GUM cl. 5.1.2)")

    # Soma das variancias (u_i^2)
    soma_var = Decimal(0)
    for c in componentes:
        soma_var += c.u_i * c.u_i

    # Soma cruzada por correlacao (se houver)
    if correlacoes:
        mapa_componentes = {c.nome: c for c in componentes}
        for nome_i, nome_j, rho in correlacoes:
            if not (Decimal("-1") <= rho <= Decimal("1")):
                raise ValueError(
                    f"correlacao ρ fora de [-1, 1]: {nome_i}-{nome_j}={rho}"
                )
            ci = mapa_componentes.get(nome_i)
            cj = mapa_componentes.get(nome_j)
            if ci is None or cj is None:
                raise ValueError(
                    f"correlacao referencia componente inexistente: "
                    f"{nome_i!r} ou {nome_j!r}"
                )
            # 2 · ρ · u_i · u_j (par (i,j), i != j)
            soma_var += Decimal(2) * rho * ci.u_i * cj.u_i

    if soma_var < 0:
        # Pode ocorrer com correlacoes negativas extremas. GUM cl. 5.2.2
        # nota 1: variancia combinada negativa indica problema no modelo.
        raise ValueError(
            f"u_c^2 < 0 ({soma_var}) — correlacoes negativas excessivas "
            f"(GUM cl. 5.2.2 nota 1; modelo precisa revisao)"
        )

    return _sqrt_decimal(soma_var)


def welch_satterthwaite(componentes: list[ComponenteEntrada]) -> int | None:
    """Graus de liberdade efetivos (GUM cl. G.4 + Welch-Satterthwaite).

    ν_eff = u_c^4 / soma(u_i^4 / ν_i)

    Componentes com ν=infinito (Tipo B sem dof declarado) NAO contribuem
    no denominador (termo zero — limite quando ν -> inf).

    Args:
      componentes: lista de ComponenteEntrada.

    Retorna:
      int >= 1 quando ha pelo menos 1 componente com dof finito.
      None quando todos componentes tem dof=infinito (resultado: usar k=2).

    Notas:
      - Resultado eh truncado pra int (cl. G.4 nota — toma valor inteiro).
      - Tabela t-Student so tem entradas inteiras; truncar reduz risco
        de subestimar k.
    """
    if not componentes:
        raise ValueError("welch_satterthwaite: lista vazia")

    # u_c eh sqrt(soma(u_i^2)) — sem correlacao (cl. G.4 assume independencia)
    soma_var = sum((c.u_i * c.u_i for c in componentes), start=Decimal(0))
    if soma_var == 0:
        # Todos os componentes sao u_i=0: cobertura indefinida; retorna None.
        return None

    denominador = Decimal(0)
    componentes_com_dof = 0
    for c in componentes:
        if c.grau_liberdade is None:
            # dof = infinito -> u_i^4 / infinito = 0 (nao contribui)
            continue
        if c.u_i == 0:
            continue
        u_i4 = (c.u_i * c.u_i) * (c.u_i * c.u_i)
        denominador += u_i4 / Decimal(c.grau_liberdade)
        componentes_com_dof += 1

    if componentes_com_dof == 0:
        # Todos componentes tem dof=infinito -> ν_eff = infinito
        return None

    if denominador == 0:
        # Componentes com dof contribuem zero (u_i=0) -> efetivamente infinito
        return None

    soma_var_quad = soma_var * soma_var
    dof_efetivo = soma_var_quad / denominador
    # Truncar pra int (GUM cl. G.4 nota)
    return int(dof_efetivo)


def fator_k_para_95(dof: int | None) -> Decimal:
    """Fator de cobertura k_95 pra 95.45% (k=2 pra normal limite).

    Args:
      dof: graus de liberdade efetivos (int >= 1) ou None (infinito).

    Retorna:
      k (Decimal) — fator de cobertura para nivel 95.45%.

    Tabela:
      None ou dof > 100 -> 2.000 (limite normal).
      1 <= dof <= 100   -> tabela GUM G.2.

    Notas:
      - Para dof fora dos pontos tabelados (ex: dof=23), usa o k da
        proxima chave INFERIOR (conservador — superestima k).
        Ex: dof=23 -> usa entrada de dof=20.
    """
    if dof is None or dof > 100:
        return _K_INFINITO_95_45
    if dof < 1:
        raise ValueError(f"fator_k_para_95: dof < 1 ({dof})")

    # Pega entrada exata se existir, senao a chave INFERIOR mais proxima
    # (conservador — k_inferior >= k_real evita subestimar U expandida).
    chaves = sorted(_TABELA_K_95_45.keys())
    if dof in _TABELA_K_95_45:
        return _TABELA_K_95_45[dof]
    # Procura chave inferior mais proxima
    inferior = max((k for k in chaves if k < dof), default=None)
    if inferior is None:
        # dof < 1 ja tratado acima; mas defensivo:
        return _TABELA_K_95_45[chaves[0]]
    return _TABELA_K_95_45[inferior]


def propagar(
    componentes: list[ComponenteEntrada],
    correlacoes: list[tuple[str, str, Decimal]] | None = None,
) -> ResultadoGUM:
    """Propagacao GUM completa — fluxo end-to-end de u_c + U expandida.

    Combina: combinar_componentes -> welch_satterthwaite -> fator_k_para_95.

    Args:
      componentes: lista de ComponenteEntrada (>= 1).
      correlacoes: opcional (ver combinar_componentes).

    Retorna:
      ResultadoGUM com u_combinada, grau_liberdade_efetivo, fator_k,
      U_expandida, nivel_confianca=0.9545.
    """
    u_c = combinar_componentes(componentes, correlacoes)
    dof_eff = welch_satterthwaite(componentes)
    k = fator_k_para_95(dof_eff)
    U = k * u_c
    return ResultadoGUM(
        u_combinada=u_c,
        grau_liberdade_efetivo=dof_eff,
        fator_k=k,
        U_expandida=U,
    )
