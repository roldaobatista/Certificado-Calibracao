"""Wave A M7 — módulo `metrologia/procedimentos-calibracao`.

Path aninhado `src/infrastructure/metrologia/procedimentos_calibracao/` (ADR-0072
— espelha o domínio). Destrava GATE-CAL-PROC-VIGENTE-PREDICATE (ADR-0066/0073):
torna real o bloqueio de emissão RBC sem procedimento técnico documentado vigente
(412 `ProcedimentoVigenteAusente` — cl. 7.2.1). Módulo-irmão de `escopos_cmc`.
"""

from __future__ import annotations

from django.apps import AppConfig


class ProcedimentosCalibracaoConfig(AppConfig):
    """M7 `metrologia/procedimentos-calibracao` — ProcedimentoCalibracao (cl. 7.2.1)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.metrologia.procedimentos_calibracao"
    label = "procedimentos_calibracao"
    verbose_name = "Procedimentos de Calibração (ISO 17025 cl. 7.2.1)"
