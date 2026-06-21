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
        # =============================================================
        # Fatia 3b — T-CT-050: consumer colaborador.desligado (fail-closed)
        # Fan-out aditivo (R8): _REGISTRY é dict[str, list] — registrar este consumer
        # NÃO engole o consumer da agenda para a mesma ação. Re-registro do MESMO fn
        # (re-entry no test runner / ready() 2x) levanta ValueError → capturado.
        # =============================================================
        from src.infrastructure.audit.outbox_worker import registrar_consumer
        from src.infrastructure.caixa_tecnico.consumers import handle_colaborador_desligado

        try:
            registrar_consumer("colaborador.desligado", handle_colaborador_desligado)
        except ValueError:
            pass  # re-registro do mesmo handler — idempotente

        # =============================================================
        # Fatia 3a — T-CT-041: wiring ColaboradorReferenciadoPort
        # Registra ColaboradorCaixaAdapter como implementação concreta de
        # ColaboradorReferenciadoPort para uso futuro pelo módulo colaboradores
        # quando o hard-delete físico for implementado (D-CT-12 / INV-CT-REF-001).
        # R11: toca colaboradores APENAS no wiring (atributo de classe).
        # =============================================================
        import logging as _logging

        _log = _logging.getLogger(__name__)
        try:
            from src.infrastructure.caixa_tecnico.colaborador_caixa_adapter import (
                ColaboradorCaixaAdapter,
            )
            from src.infrastructure.colaboradores.views import ColaboradorViewSet

            # NOTA HONESTA: nenhum fluxo de colaboradores lê este atributo HOJE — o
            # `destroy` atual é DESLIGAMENTO lógico, não hard-delete físico. Registro
            # fail-open lazy (ADR-0066) PRONTO para GATE-CT-COLABORADOR-REFERENCIADO
            # (consumo pelo hard-delete pendente).
            ColaboradorViewSet._referenciado_caixa_tecnico_port = (  # type: ignore[attr-defined]
                ColaboradorCaixaAdapter()
            )
        except Exception as wiring_exc:
            # Wiring de boot — falha silenciosa intencional (fail-safe ADR-0066).
            # DELETE físico não é exposto via API (destroy = desligamento lógico);
            # o schema de colaboradores tem trigger defensivo como salvaguarda.
            _log.warning(
                "CaixaTecnicoConfig.ready: falha no wiring de ColaboradorReferenciadoPort "
                "(D-CT-12 / T-CT-041): %s. Adapter do caixa_tecnico fica indisponível p/ "
                "futura consulta de hard-delete (GATE-CT-COLABORADOR-REFERENCIADO).",
                wiring_exc,
            )
