"""AppConfig da frente caixa_tecnico (Fatia 1b — T-CT-020).

Caminho FLAT: ``src/infrastructure/caixa_tecnico/``.
Núcleo autossuficiente (schema + portas FAKE) em Fatia 1b+2;
adapters reais cross-módulo em Fatia 3a; eventos em Fatia 3b.

App label: ``caixa_tecnico`` (igual ao slug do módulo).
"""

from __future__ import annotations

from django.apps import AppConfig


class CaixaTecnicoConfig(AppConfig):
    """Configuração da app caixa_tecnico."""

    name = "src.infrastructure.caixa_tecnico"
    label = "caixa_tecnico"
    verbose_name = "Caixa do Técnico"

    def ready(self) -> None:
        # TODO Fatia 3b: registrar consumers
        #   - colaborador.desligado → handle_colaborador_desligado (fail-closed desligado_em)
        pass
