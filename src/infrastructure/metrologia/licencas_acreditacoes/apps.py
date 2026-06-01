"""Wave A M9 — módulo `metrologia/licencas-acreditacoes` (documentos regulatórios da empresa).

Path aninhado `src/infrastructure/metrologia/licencas_acreditacoes/` (ADR-0072 — espelha
o domínio). Fonte rica da vigência da acreditação CGCRE (ADR-0079); popula o cache
`Tenant.acreditacao_vigencia_fim` via `aplicar_evento_cgcre` → fecha
GATE-CER-CGCRE-VIG-DATA-POPULAR do M8.
"""

from __future__ import annotations

from django.apps import AppConfig


class LicencasAcreditacoesConfig(AppConfig):
    """M9 `metrologia/licencas-acreditacoes` — DocumentoRegulatorio + revisões WORM."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.metrologia.licencas_acreditacoes"
    label = "licencas_acreditacoes"
    verbose_name = "Licenças, Acreditações e Autorizações da Empresa (ISO 17025 / CGCRE)"
