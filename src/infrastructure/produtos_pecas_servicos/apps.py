"""Wave A — frente `produtos-pecas-servicos` + TabelaPreco (#2 da cadeia de preço).

Raiz própria `src/infrastructure/produtos_pecas_servicos/` (path achatado —
D-PPS-1; ADR-0072 só normatiza metrologia). Catálogo central (4 tipos de item)
com preço de LISTA versionado imutável (INV-026) + TabelaPreco de VENDA vigente
fail-closed (ADR-0081 — porta `preco_para_os` que a OS avulsa consome via
GATE-PPS-WIREIN-OS).
"""

from __future__ import annotations

from django.apps import AppConfig


class ProdutosPecasServicosConfig(AppConfig):
    """Frente `produtos-pecas-servicos` (ADR-0081; plano-dependencia-sistema #2)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.produtos_pecas_servicos"
    label = "produtos_pecas_servicos"
    verbose_name = "Catálogo (produtos, peças, serviços, kits) + Tabela de Preço"
