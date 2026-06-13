"""Portas (Protocols) do módulo `precificacao` (T-PRC-013).

`CustoProvider`: contrato para obter custo real de um item (Wave A = stub).
`StubCustoProvider`: implementação de fallback que sinaliza ausência EXPLÍCITA
  de custo — NUNCA retorna 0 silencioso (INV-PRC-CUSTO-EXPLICITO / D-PRC-5).

Molde: `CoberturaEscopoPort` da calibração (mesmo padrão Protocol runtime_checkable).
Provider real chega com `custeio-real` (N7) sem mudar este contrato.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID

from .erros import CustoIndisponivel


@runtime_checkable
class CustoProvider(Protocol):
    """Porta para obtenção do custo real de um item de catálogo (D-PRC-5).

    Retorna o custo em BRL (Decimal) quando disponível.
    Levanta `CustoIndisponivel` quando o provider não tem dado para o item
    (INV-PRC-CUSTO-EXPLICITO: ausência é EXPLÍCITA, nunca 0 silencioso).

    `disponivel()` indica se o provider real está conectado (True = provider real;
    False = stub). Usado pelo use case `publicar_regra` para bloquear COST_PLUS
    sob stub em tempo de CONFIGURAÇÃO (D-PRC-6 / INV-PRC-COSTPLUS-STUB).

    Args:
      tenant_id: UUID do tenant isolado (multi-tenancy ADR-0002).
      item_id: UUID do item de catálogo a costar.

    Returns:
      Decimal com custo estimado em BRL, escala 2.

    Raises:
      CustoIndisponivel: quando o custo não está disponível para o item.
    """

    def __call__(self, *, tenant_id: UUID, item_id: UUID) -> Decimal: ...

    def disponivel(self) -> bool:
        """Retorna True se o provider real está disponível; False se stub."""
        ...


class StubCustoProvider:
    """Implementação stub do `CustoProvider` para Wave A (D-PRC-5).

    Sempre levanta `CustoIndisponivel` — sinaliza explicitamente que o provider
    real não está disponível (INV-PRC-CUSTO-EXPLICITO). NUNCA retorna 0.

    Injetado na view até `custeio-real` (N7) substituir sem mudar contrato.
    """

    def disponivel(self) -> bool:
        """Stub: sempre retorna False (provider real não disponível — D-PRC-6)."""
        return False

    def __call__(self, *, tenant_id: UUID, item_id: UUID) -> Decimal:
        """Levanta CustoIndisponivel para todo item — stub sem dados reais.

        Nunca retorna 0 silencioso. Ausência de custo real é explícita:
        o motor usa CustoIndisponivel para marcar origem=INDISPONIVEL e
        semáforo INDISPONIVEL no resultado (TL-PRC-05).
        """
        raise CustoIndisponivel(
            f"StubCustoProvider: custo indisponível para item {item_id} "
            f"(tenant {tenant_id}) — provider real não configurado "
            "(INV-PRC-CUSTO-EXPLICITO / GATE-PRC-CUSTEIO-REAL)."
        )


# Alias: views Wave A importam `CustoProviderStub` (nome alternativo usado na geração do código)
CustoProviderStub = StubCustoProvider
