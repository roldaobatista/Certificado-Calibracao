"""Value Objects do domínio Orçamentos — T-ORC-011.

Cria ``Desconto`` e ``CondicoesPagamento`` (VOs frozen novos).
Os demais VOs usados no módulo são importados diretamente de seus módulos de origem:
  - ``Dinheiro``                → ``src.domain.shared.value_objects``
  - ``JanelaVigencia``          → ``src.domain.shared.value_objects``
  - ``ReferenciaPIIAnonimizavel`` → ``src.domain.shared.value_objects``
  - ``PrecoResolvido``          → ``src.domain.produtos_pecas_servicos.entities``

Refs:
  D-ORC-1  — Snapshot de preço = PrecoResolvido
  D-ORC-4  — Cliente via ReferenciaPIIAnonimizavel
  spec §4  — VOs: Dinheiro / Desconto / CondicoesPagamento

Zero imports Django / infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

# =====================================================================
# DESCONTO
# =====================================================================


@dataclass(frozen=True, slots=True)
class Desconto:
    """Desconto aplicado a um item ou ao total do orçamento.

    Suporta desconto percentual e/ou valor absoluto.
    Ambos podem coexistir; a aplicação decide a precedência
    (normalmente ``calcular_precos`` do módulo ``precificacao`` resolve).

    Invariantes:
      - ``percentual`` ∈ [0, 100] (Decimal).
      - ``valor_centavos`` ≥ 0 (int).
      - Pelo menos um dos dois deve ser não-nulo (não criar Desconto "vazio").

    Refs: spec §4 (VO modelo PRD), D-ORC-10 (cálculo server-side).
    """

    percentual: Decimal
    """Percentual de desconto: 0 a 100 (ex.: Decimal('15.50') = 15,5%)."""

    valor_centavos: int
    """Valor fixo de desconto em centavos (complementar ao percentual)."""

    def __post_init__(self) -> None:
        # Valida tipo
        if not isinstance(self.percentual, Decimal):
            try:
                object.__setattr__(self, "percentual", Decimal(str(self.percentual)))
            except (InvalidOperation, TypeError) as exc:
                raise ValueError(
                    f"Desconto.percentual deve ser Decimal conversível: {self.percentual!r}"
                ) from exc
        if not isinstance(self.valor_centavos, int):
            raise ValueError(
                f"Desconto.valor_centavos deve ser int: {type(self.valor_centavos).__name__}"
            )
        # Invariantes de domínio
        if not (Decimal("0") <= self.percentual <= Decimal("100")):
            raise ValueError(
                f"Desconto.percentual deve estar em [0, 100]: {self.percentual}"
            )
        if self.valor_centavos < 0:
            raise ValueError(
                f"Desconto.valor_centavos não pode ser negativo: {self.valor_centavos}"
            )
        if self.percentual == Decimal("0") and self.valor_centavos == 0:
            raise ValueError(
                "Desconto não pode ter percentual=0 e valor_centavos=0 simultaneamente."
            )

    @classmethod
    def por_percentual(cls, percentual: Decimal) -> Desconto:
        """Cria desconto apenas percentual (valor_centavos=0)."""
        return cls(percentual=percentual, valor_centavos=0)

    @classmethod
    def por_valor(cls, valor_centavos: int) -> Desconto:
        """Cria desconto apenas por valor fixo (percentual=0)."""
        return cls(percentual=Decimal("0"), valor_centavos=valor_centavos)

    def __str__(self) -> str:
        partes = []
        if self.percentual:
            partes.append(f"{self.percentual}%")
        if self.valor_centavos:
            partes.append(f"R${self.valor_centavos / 100:.2f}")
        return " + ".join(partes)


# =====================================================================
# CONDICOES DE PAGAMENTO
# =====================================================================

_FORMAS_VALIDAS = frozenset({
    "dinheiro",
    "pix",
    "cartao_credito",
    "cartao_debito",
    "boleto",
    "transferencia",
    "cheque",
    "a_prazo",
})


@dataclass(frozen=True, slots=True)
class CondicoesPagamento:
    """Condições de pagamento negociadas no orçamento.

    Captura o acordo comercial de forma que fique registrado no snapshot
    da versão do orçamento (D-ORC-8) e possa ser referenciado na emissão
    da NF/fatura futura (US-ORC-010 diferido).

    Invariantes:
      - ``parcelas`` ≥ 1.
      - ``forma_pagamento`` pertence ao conjunto de formas válidas.
      - ``intervalo_dias`` ≥ 0; irrelevante quando parcelas=1 (mas aceito).
      - ``dias_vencimento_primeira`` ≥ 0 (0 = à vista / no ato).

    Refs: spec §4 (VO CondicoesPagamento modelo PRD), D-ORC-10.
    """

    parcelas: int
    """Número de parcelas (mínimo 1 = à vista)."""

    forma_pagamento: str
    """Forma: 'pix', 'boleto', 'cartao_credito', 'cartao_debito', 'dinheiro',
    'transferencia', 'cheque', 'a_prazo'."""

    dias_vencimento_primeira: int = 0
    """Dias até o vencimento da 1ª parcela a partir da emissão (0 = no ato)."""

    intervalo_dias: int = 30
    """Intervalo em dias entre parcelas (irrelevante quando parcelas=1)."""

    observacoes: str | None = None
    """Condições especiais livres (limite 300 chars)."""

    def __post_init__(self) -> None:
        if not isinstance(self.parcelas, int) or self.parcelas < 1:
            raise ValueError(
                f"CondicoesPagamento.parcelas deve ser int ≥ 1: {self.parcelas!r}"
            )
        forma = (self.forma_pagamento or "").strip().lower()
        if forma not in _FORMAS_VALIDAS:
            raise ValueError(
                f"CondicoesPagamento.forma_pagamento inválida: {self.forma_pagamento!r}. "
                f"Válidas: {sorted(_FORMAS_VALIDAS)}"
            )
        object.__setattr__(self, "forma_pagamento", forma)
        if not isinstance(self.dias_vencimento_primeira, int) or self.dias_vencimento_primeira < 0:
            raise ValueError(
                f"CondicoesPagamento.dias_vencimento_primeira deve ser int ≥ 0: "
                f"{self.dias_vencimento_primeira!r}"
            )
        if not isinstance(self.intervalo_dias, int) or self.intervalo_dias < 0:
            raise ValueError(
                f"CondicoesPagamento.intervalo_dias deve ser int ≥ 0: {self.intervalo_dias!r}"
            )
        if self.observacoes is not None and len(self.observacoes) > 300:
            raise ValueError(
                f"CondicoesPagamento.observacoes excede 300 chars "
                f"(recebido {len(self.observacoes)})."
            )

    @classmethod
    def a_vista_pix(cls) -> CondicoesPagamento:
        """Atalho: pagamento à vista via Pix."""
        return cls(parcelas=1, forma_pagamento="pix", dias_vencimento_primeira=0)

    @classmethod
    def parcelado(
        cls,
        parcelas: int,
        forma: str,
        intervalo_dias: int = 30,
        primeira_em_dias: int = 30,
    ) -> CondicoesPagamento:
        """Atalho: parcelado com intervalo fixo."""
        return cls(
            parcelas=parcelas,
            forma_pagamento=forma,
            dias_vencimento_primeira=primeira_em_dias,
            intervalo_dias=intervalo_dias,
        )

    def __str__(self) -> str:
        if self.parcelas == 1:
            return f"À vista — {self.forma_pagamento}"
        return (
            f"{self.parcelas}x {self.forma_pagamento} "
            f"(1ª em {self.dias_vencimento_primeira}d, "
            f"intervalo {self.intervalo_dias}d)"
        )
