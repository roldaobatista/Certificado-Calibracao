"""Marco 3 — nucleo operacional (Ordens de Servico com Atividades)."""

from __future__ import annotations

from django.apps import AppConfig


class OrdensServicoConfig(AppConfig):
    """Wave A Marco 3 — modulo `ordens_servico` (operacao/os)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.ordens_servico"
    label = "ordens_servico"
    verbose_name = "Ordens de Servico (operacao)"
