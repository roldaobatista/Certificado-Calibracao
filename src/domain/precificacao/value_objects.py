"""Value objects do módulo `precificacao` (T-PRC-011).

`Percentual`: 0..100, escala 2, ROUND_HALF_EVEN. Conversão pra fração documentada
(TL-PRC-18 — determinismo bit-a-bit cross-versão de motor).

`CalculoPrecoResultado`: frozen autossuficiente para replay e carimbo pelo
consumidor (D-PRC-9 / INV-026). `preco_final` é Decimal ≥ 0 PRÓPRIO — NUNCA
reusa VO `Preco > 0` da PPS (cortesia 100% precisa de preco_final = 0; D-PRC-13).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID

from src.domain.produtos_pecas_servicos.entities import PrecoResolvido

from .enums import Alcada, OrigemCusto, Semaforo

_ESCALA = Decimal("0.01")

_ZERO = Decimal("0")


@dataclass(frozen=True)
class Percentual:
    """Percentual entre 0 e 100 (inclusive), escala 2, ROUND_HALF_EVEN.

    Uso canônico: margem_alvo, margem_piso, desconto_pct, alçada de faixa.

    Conversão pra fração: `pct.fracao()` → `valor / 100` (Decimal exato).
    A operação DEVE ser feita via este método para garantir determinismo bit-a-bit
    cross-versão de motor (TL-PRC-18 — denominador 100 em Decimal não tem deriva).

    Exemplos:
      Percentual(Decimal("10.50")).fracao() == Decimal("0.105")  # exato
      Percentual(Decimal("100")).fracao()  == Decimal("1")
      Percentual(Decimal("0")).fracao()    == Decimal("0")
    """

    valor: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            raise TypeError(f"Percentual.valor deve ser Decimal, veio {type(self.valor)!r}")
        normalizado = self.valor.quantize(_ESCALA, rounding=ROUND_HALF_EVEN)
        if normalizado < _ZERO or normalizado > Decimal("100"):
            raise ValueError(
                f"Percentual deve ser 0..100 (veio {self.valor}) — "
                "INV-PRC-FAIXAS-CONTIGUAS / D-PRC-3"
            )
        object.__setattr__(self, "valor", normalizado)

    def fracao(self) -> Decimal:
        """Converte percentual para fração multiplicadora (divide por 100).

        Determinístico: `Decimal("100")` exato — sem deriva de ponto flutuante.
        Sempre use este método nas fórmulas de cálculo (TL-PRC-18).
        """
        return self.valor / Decimal("100")

    def __str__(self) -> str:
        return f"{self.valor}%"


@dataclass(frozen=True)
class ItemCalculado:
    """Resultado do cálculo para UM item da cesta (campo de `CalculoPrecoResultado`).

    preco_base: PrecoResolvido embutido (refs probatórias completas).
    preco_final: Decimal ≥ 0 PRÓPRIO — NUNCA VO Preco > 0 (D-PRC-13 / INV-PPS-PRECO-POSITIVO).
    desconto_pct: percentual de desconto aplicado (0..100).
    semaforo: semáforo de margem visível ao vendedor (D-PRC-4).
    margem_estimada: margem estimada em % (SÓ com precificacao.ver_margem — D-PRC-4).
    custo_estimado: custo estimado em BRL (SÓ com precificacao.ver_margem — D-PRC-4).
    preco_minimo: piso monetário calculável (visível a qualquer papel com calcular — D-PRC-4).
    origem_custo: proveniência do custo usado.
    custo_declarado_em: data do custo manual (staleness visível — TL-PRC-07).
    sem_regra_formacao: True quando não há regra vigente para este item (TL-PRC-05).
    cortesia: True quando desconto_pct == 100 (D-PRC-13).
    """

    preco_base: PrecoResolvido
    preco_final: Decimal  # ≥ 0 validado em __post_init__
    desconto_pct: Percentual
    semaforo: Semaforo
    origem_custo: OrigemCusto
    sem_regra_formacao: bool
    cortesia: bool
    margem_estimada: Decimal | None = None
    custo_estimado: Decimal | None = None
    preco_minimo: Decimal | None = None
    custo_declarado_em: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.preco_final, Decimal):
            raise TypeError(
                f"ItemCalculado.preco_final deve ser Decimal, veio {type(self.preco_final)!r}"
            )
        normalizado = self.preco_final.quantize(_ESCALA, rounding=ROUND_HALF_EVEN)
        if normalizado < _ZERO:
            raise ValueError(
                f"ItemCalculado.preco_final deve ser >= 0 (veio {self.preco_final}) — "
                "D-PRC-13: cortesia 100% = preco_final=0 é legítimo."
            )
        object.__setattr__(self, "preco_final", normalizado)


@dataclass(frozen=True)
class CalculoPrecoResultado:
    """Resultado autossuficiente do motor de cálculo por CESTA (D-PRC-9/11/T-PRC-011).

    FROZEN e AUTOSSUFICIENTE para replay e carimbo pelo consumidor (INV-026).
    Carrega refs probatórias de versão de motor, faixas e parâmetros para que
    o consumidor (orçamento/OS) possa verificar determinismo sem consultar banco.

    Campos:
      itens: resultados calculados por item da cesta.
      componentes_faltantes: IDs de items esperados pelo perfil mas ausentes na cesta
                             (D-PRC-2 / ModoMontagem.COMPONENTES_CHECKLIST).
      avisos: textos de aviso (ex: aviso_texto do perfil em FECHADO_COM_AVISO).
      alcada_exigida: alçada máxima necessária considerando todos os itens da cesta.
      motor_versao: versão do motor de cálculo (ref para determinismo AC-PRC-002-3).
      faixas_versao: hash de versão do conjunto de faixas usado no cálculo.
      imposto_ref: (id, versao) do Imposto usado na simulação fiscal.
      parametros_versao: versão dos ParametrosPrecificacaoTenant usados.
      eco_entradas: espelho das entradas do motor (km, desconto_pct, modo_montagem,
                    parcelas) para replay bit-a-bit.
    """

    itens: tuple[ItemCalculado, ...]
    componentes_faltantes: tuple[UUID, ...]
    avisos: tuple[str, ...]
    alcada_exigida: Alcada
    motor_versao: str
    faixas_versao: str
    imposto_ref: tuple[UUID, int] | None  # (id, versao_n) do Imposto vigente
    parametros_versao: int
    eco_entradas: dict[str, str]  # entradas serializadas para replay
