"""Wave A M6 — módulo `metrologia/escopos-cmc` (escopo de acreditação CGCRE + CMC).

Path aninhado `src/infrastructure/metrologia/escopos_cmc/` (ADR-0072 — espelha o
domínio `src/domain/metrologia/escopos_cmc/`). Destrava GATE-CAL-CMC-PREDICATE
(ADR-0066/0073): torna o bloqueio de emissão RBC fora do escopo real.
"""

from __future__ import annotations

from django.apps import AppConfig


class EscoposCmcConfig(AppConfig):
    """M6 `metrologia/escopos-cmc` — EscopoCMC (ADR-0040/0074/0075)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.metrologia.escopos_cmc"
    label = "escopos_cmc"
    verbose_name = "Escopos de Acreditação CMC (ISO 17025 / CGCRE-RBC)"
