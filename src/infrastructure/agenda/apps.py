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
        # TODO Fatia 3: registrar consumers cross-módulo
        # (os.aberta/cancelada/reaberta/atividade_concluida/atividade_cancelada,
        # colaborador.desligado/papel_atribuido/papel_revogado,
        # tenant.rt.trocado/rt.substituicao_declarada/rt.substituicao_encerrada)
        # usando registrar_consumer do outbox_worker (fan-out, PLAN-AGE-07).
        pass
