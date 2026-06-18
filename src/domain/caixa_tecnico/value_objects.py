"""Value objects do domínio caixa_tecnico (Fatia 1a — T-CT-012).

Reusa ``Dinheiro`` e ``ReferenciaPIIAnonimizavel`` de ``src.domain.shared.value_objects``.
Zero Django. Zero I/O.

Refs: D-CT-2/6; spec §4.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.shared.value_objects import (  # reexportado para conveniência
    Dinheiro,
    ReferenciaPIIAnonimizavel,
)

from .enums import DirecaoPrestacao

__all__ = [
    "Periodo",
    "Coordenada",
    "ResultadoSaldo",
    # reexportados de shared
    "Dinheiro",
    "ReferenciaPIIAnonimizavel",
]


@dataclass(frozen=True)
class Periodo:
    """Intervalo fechado de datas [de, ate].

    Imutável. Levanta ``ValueError`` se ``de >= ate`` (intervalo vazio ou invertido).

    Usado no fechamento de prestação de contas para delimitar o período
    e bloquear novos lançamentos após o fechamento (D-CT-8 / INV-CT-PRESTACAO-001).
    """

    de: date
    ate: date

    def __post_init__(self) -> None:
        if self.de >= self.ate:
            raise ValueError(
                f"Periodo inválido: 'de' ({self.de}) deve ser anterior a 'ate' ({self.ate})"
            )

    def contem(self, data: date) -> bool:
        """Retorna True se a data está dentro do período [de, ate]."""
        return self.de <= data <= self.ate


@dataclass(frozen=True)
class Coordenada:
    """Coordenada geográfica GPS (opcional na despesa — D-CT-6 / INV-LGPD-CONSENT-001).

    Imutável. Validação de limites geográficos:
      - lat: -90 ≤ lat ≤ 90
      - lng: -180 ≤ lng ≤ 180

    Nunca lida do payload nem do EXIF — vem SOMENTE do opt-in server-side
    (``ConsentimentoGpsPort.opt_in_vigente``). GPS ausente = ``None`` no campo da entidade.
    Retenção curta: fechamento da prestação + 90 dias (crypto-shredding via
    ``ReferenciaPIIAnonimizavel``).
    """

    lat: float
    lng: float

    def __post_init__(self) -> None:
        if not (-90 <= self.lat <= 90):
            raise ValueError(f"Coordenada.lat inválido: {self.lat} (esperado -90 ≤ lat ≤ 90)")
        if not (-180 <= self.lng <= 180):
            raise ValueError(f"Coordenada.lng inválido: {self.lng} (esperado -180 ≤ lng ≤ 180)")


@dataclass(frozen=True)
class ResultadoSaldo:
    """Resultado do cálculo de saldo do caixa do técnico (D-CT-2 / INV-CT-SALDO-001).

    Imutável. Saldo é DERIVADO on-read — nunca campo mutável no banco.
    Derivação: saldo_final = total_adiantado - total_despesas
    Direção derivada automaticamente:
      saldo_final > 0 → tenant_deve (tenant deve reembolsar o técnico)
      saldo_final < 0 → tecnico_deve (técnico deve devolver ao tenant)
      saldo_final == 0 → quitado

    Convenção de sinal (AC T-CT-013):
      calcular_saldo([adiant_500], [despesa_300]) → saldo=200, direcao=tenant_deve
    """

    total_adiantado: Dinheiro
    total_despesas: Dinheiro
    saldo_final: Dinheiro
    direcao: DirecaoPrestacao

    @classmethod
    def calcular(
        cls,
        total_adiantado: Dinheiro,
        total_despesas: Dinheiro,
    ) -> ResultadoSaldo:
        """Fábrica: calcula saldo_final e deriva direcao automaticamente."""
        saldo = total_adiantado - total_despesas
        if saldo.centavos > 0:
            direcao = DirecaoPrestacao.TENANT_DEVE
        elif saldo.centavos < 0:
            direcao = DirecaoPrestacao.TECNICO_DEVE
        else:
            direcao = DirecaoPrestacao.QUITADO
        return cls(
            total_adiantado=total_adiantado,
            total_despesas=total_despesas,
            saldo_final=saldo,
            direcao=direcao,
        )
