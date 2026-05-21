"""App de Responsavel Tecnico do tenant (US-EQP-007 / P-EQP-R10 BLOQUEANTE).

NIT-DICLA-021 (signatario autorizado) + ISO/IEC 17025 cl. 5.6 + cl. 6.2.

Modelo separado (e nao dentro de `equipamentos/` nem `tenant/`) por 2
razoes:
- RT e cross-cutting: usado por equipamentos (versionamento US-EQP-002),
  certificados (Wave A), competencias gestor_qualidade (US-EQP-002b),
  notificacoes ANPD/CGCRE. Acoplar a `equipamentos/` cria ciclo.
- Tabela INSERT-only + trigger anti-mutation — politica de auditoria
  proxima da F-A `audit/`, nao do dominio tenant.

Spec: docs/faseamento/M2-equipamentos/spec.md §US-EQP-007
Plan: docs/faseamento/M2-equipamentos/plan.md §P-EQP-R10
"""

from __future__ import annotations

from django.apps import AppConfig


class ResponsavelTecnicoConfig(AppConfig):
    """US-EQP-007 — RT do tenant (NIT-DICLA-021)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.responsavel_tecnico"
    label = "responsavel_tecnico"
    verbose_name = "Responsavel Tecnico (US-EQP-007)"
