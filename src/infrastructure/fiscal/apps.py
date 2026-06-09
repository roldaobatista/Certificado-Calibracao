"""Wave A — frente `fiscal/NFS-e` (emissão de nota fiscal de serviço).

Raiz própria `src/infrastructure/fiscal/` (domínio `financeiro` — NÃO sob
`metrologia/`; ADR-0072 só normatiza metrologia; TL-08). Núcleo agnóstico de
país/fornecedor (ADR-0008) com a trava metrológica por perfil no use case
(ADR-0073). Deadline regulatório 01/09/2026 (Padrão Nacional NFS-e).
"""

from __future__ import annotations

from django.apps import AppConfig


class FiscalConfig(AppConfig):
    """Frente `fiscal` — `NotaFiscalServico` (ADR-0008/0067/0073)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.fiscal"
    label = "fiscal"
    verbose_name = "Fiscal (NFS-e de serviço)"
