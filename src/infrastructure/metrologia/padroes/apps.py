"""Wave A M5 — modulo `metrologia/padroes` (padrao metrologico do laboratorio).

Path aninhado `src/infrastructure/metrologia/padroes/` (ADR-0072 — espelha o
dominio `src/domain/metrologia/padroes/`). M4 `calibracao` ficou achatado e e
divida conhecida (NAO renomear — ADR-0072).
"""

from __future__ import annotations

from django.apps import AppConfig


class PadroesConfig(AppConfig):
    """M5 `metrologia/padroes` — agregado PadraoMetrologico (ADR-0040)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.metrologia.padroes"
    label = "padroes"
    verbose_name = "Padroes Metrologicos (ISO 17025 cl. 6.4/6.5)"
