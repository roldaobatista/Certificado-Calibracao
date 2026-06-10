"""Wave A — frente `configuracoes-sistema` (raiz da cadeia de preço).

Raiz própria `src/infrastructure/configuracoes_sistema/` (path achatado — ADR-0072
só normatiza metrologia). Três agregados do núcleo: `Empresa`/`Filial` (cadastro
base, INV-036/037), `Imposto`+`RegimeTributario` (catálogo tributário versionado
imutável, INV-CFG-IMPOSTO-*) e `SerieDocumento` (numeração local em 2 regimes por
tipo — ADR-0080, INV-028/INV-CFG-NUM-ATOMICA).
"""

from __future__ import annotations

from django.apps import AppConfig


class ConfiguracoesSistemaConfig(AppConfig):
    """Frente `configuracoes-sistema` (ADR-0080; plano-dependencia-sistema #1)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.configuracoes_sistema"
    label = "configuracoes_sistema"
    verbose_name = "Configurações do Sistema (empresa, tributos, séries)"
