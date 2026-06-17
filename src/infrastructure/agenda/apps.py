"""Frente `agenda` — calendário multi-técnico + jornada UMC (D-AGE-1).

Path flat ``src/infrastructure/agenda/`` com ``label="agenda"`` (espelha
``ordens_servico`` e ``contas_receber``). Domínio em
``src/domain/operacao/agenda/``.
"""

from __future__ import annotations

from django.apps import AppConfig


class AgendaConfig(AppConfig):
    """Frente `agenda` — alocação de atividades, bloqueios, jornada UMC."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.agenda"
    label = "agenda"
    verbose_name = "Agenda (calendário multi-técnico, jornada UMC)"

    def ready(self) -> None:
        """Registra consumers cross-módulo no bus (Fatia 3b — T-AGE-044) e
        wiring de ColaboradorReferenciadoPort (Fatia 3c — T-AGE-045).

        Fan-out aditivo (R8): _REGISTRY já é dict[str, list] — registrar
        consumer da agenda NÃO engole consumers existentes de outros módulos.
        Cada ``registrar_consumer`` em ``try/except ValueError: pass`` —
        re-registro do MESMO fn levanta ValueError (molde ordens_servico/apps.py).

        Eventos consumidos:
          os.aberta / os.cancelada / os.reaberta /
          os.atividade_concluida / os.atividade_cancelada
          colaborador.desligado / colaborador.papel_atribuido / colaborador.papel_revogado
          tenant.rt.trocado

        DÉBITO (RBC-AGE-04 / GATE-RTSUBSTITUICAO-FORMAL):
          tenant.rt.substituicao_declarada / tenant.rt.substituicao_encerrada
          NÃO existem no catálogo canônico (modelo RTSubstituicao não criado em Wave A).
          Quando forem criados: adicionar a ACOES_RT + registrar aqui.

        GATE (ColaboradorReferenciadoPort — D-AGE-12 / Fatia 3c):
          O mecanismo de consulta de ports no hard-delete físico de colaboradores
          NÃO existe em colaboradores (módulo FECHADO — só desligamento/soft-delete
          está implementado no destroy() da view). O wiring abaixo registra a
          implementação concreta para uso futuro quando o hard-delete for implementado.
          Por R11 (módulo fechado), tocamos colaboradores APENAS no wiring:
          injetamos via atributo de classe da view (try/except — não falha o boot).
        """
        from src.infrastructure.audit.outbox_worker import registrar_consumer

        from .consumers.colaborador_eventos import (
            handle_colaborador_desligado,
            handle_papel_atribuido,
            handle_papel_revogado,
        )
        from .consumers.os_eventos import (
            handle_os_aberta,
            handle_os_atividade_cancelada,
            handle_os_atividade_concluida,
            handle_os_cancelada,
            handle_os_reaberta,
        )
        from .consumers.rt_eventos import handle_tenant_rt_trocado

        _MAPA_CONSUMERS = {
            # OS (fan-out com os consumers existentes de ordens_servico — R8)
            "os.aberta": handle_os_aberta,
            "os.cancelada": handle_os_cancelada,
            "os.reaberta": handle_os_reaberta,
            "os.atividade_concluida": handle_os_atividade_concluida,
            "os.atividade_cancelada": handle_os_atividade_cancelada,
            # Colaborador
            "colaborador.desligado": handle_colaborador_desligado,
            "colaborador.papel_atribuido": handle_papel_atribuido,
            "colaborador.papel_revogado": handle_papel_revogado,
            # RT — apenas tenant.rt.trocado (substituicao_* aguarda GATE-RTSUBSTITUICAO-FORMAL)
            "tenant.rt.trocado": handle_tenant_rt_trocado,
        }
        for acao, fn in _MAPA_CONSUMERS.items():
            try:
                registrar_consumer(acao, fn)
            except ValueError:
                # Re-registro do mesmo fn (re-entry em test runner). Idempotente.
                pass

        # =============================================================
        # Fatia 3c — T-AGE-045: wiring ColaboradorReferenciadoPort
        # Registra AgendaColaboradorReferenciadoAdapter como implementação
        # concreta de ColaboradorReferenciadoPort para uso futuro pelo módulo
        # colaboradores quando o hard-delete físico for implementado (D-AGE-12).
        # R11: toca colaboradores APENAS no wiring (atributo de classe).
        # try/except BaseException: boot deve continuar mesmo se wiring falhar.
        # =============================================================
        import logging as _logging

        _log = _logging.getLogger(__name__)
        try:
            from src.infrastructure.agenda.referenciado import (
                AgendaColaboradorReferenciadoAdapter,
            )
            from src.infrastructure.colaboradores.views import ColaboradorViewSet

            # Registra a instância concreta no atributo de classe (R11 — toca
            # colaboradores SÓ no wiring). NOTA HONESTA: nenhum fluxo de colaboradores
            # lê este atributo HOJE — o `destroy` atual é DESLIGAMENTO lógico, não
            # hard-delete físico. Registro fail-open lazy (ADR-0066) PRONTO para
            # GATE-AGE-COLABORADOR-REFERENCIADO (consumo pelo hard-delete pendente).
            ColaboradorViewSet._referenciado_agenda_port = (  # type: ignore[attr-defined]
                AgendaColaboradorReferenciadoAdapter()
            )
        except Exception as wiring_exc:
            # Wiring de boot — falha silenciosa intencional (fail-safe ADR-0066).
            # DELETE físico não é exposto via API (destroy = desligamento lógico);
            # o schema de colaboradores tem `0003_trigger_defensivo` como salvaguarda.
            _log.warning(
                "AgendaConfig.ready: falha no wiring de ColaboradorReferenciadoPort "
                "(D-AGE-12 / T-AGE-045): %s. Adapter de agenda fica indisponível p/ futura "
                "consulta de hard-delete (GATE-AGE-COLABORADOR-REFERENCIADO).",
                wiring_exc,
            )
