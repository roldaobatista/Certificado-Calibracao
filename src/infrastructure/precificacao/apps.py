"""Wave A — frente `precificacao` (#3 da cadeia de preço).

Raiz própria `src/infrastructure/precificacao/` (path achatado —
D-PRC-1; ADR-0072 só normatiza metrologia). Motor de formação de
preço por item (PRECO_FIXO/MARGEM_ALVO/COST_PLUS via stub Wave A),
faixas de aprovação de desconto, pedido one-shot WORM e vínculo
cliente→tabela de preço (ADR-0081 / D-PRC-12).
"""

from __future__ import annotations

from django.apps import AppConfig


class PrecificacaoConfig(AppConfig):
    """Frente `precificacao` (D-PRC-1; plano-dependencia-sistema #3)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.precificacao"
    label = "precificacao"
    verbose_name = "Precificação (regras de formação, faixas, aprovação de desconto)"
