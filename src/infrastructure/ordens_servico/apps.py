"""Marco 3 — nucleo operacional (Ordens de Servico com Atividades)."""

from __future__ import annotations

from django.apps import AppConfig


class OrdensServicoConfig(AppConfig):
    """Wave A Marco 3 — modulo `ordens_servico` (operacao/os)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.ordens_servico"
    label = "ordens_servico"
    verbose_name = "Ordens de Servico (operacao)"

    def ready(self) -> None:
        """Registra predicates ABAC do modulo (T-OS-023..027 / Fase 3).

        Escopo de cada predicate (T-FB-01 / AC-FB-006-2 — escopo declarado
        e propriedade de quem escreve o predicate):

        - `rt_competencia_cobre`: actions onde o executor designado precisa
          estar competente pra grandeza. Self-guard: `resource.grandeza`
          vazio => nao aplica (atividade nao-calibracao).
        - `tenant_dentro_escopo_acreditado`: actions que abrem nova
          atividade calibracao/inmetro. STUB Wave A — GATE-RBC-ESCOPO-1.
        - `pode_estender_janela_cal_link_atividade`: action especifica de
          estender watchdog.
        - `pode_dispensar_aceite`: action especifica de dispensa formal.
        - `pode_criar_os_produtiva_balancas`: TODA action `os.abrir`
          (predicate self-guarda — soh aplica ao tenant Balancas).
        """
        from src.infrastructure.authz.predicates import register_predicate

        from .predicates_os import (
            pode_criar_os_produtiva_balancas,
            pode_dispensar_aceite,
            pode_estender_janela_cal_link_atividade,
            rt_competencia_cobre,
            tenant_dentro_escopo_acreditado,
        )

        # rt_competencia_cobre — escopo amplo (4 actions); self-guarda
        # ja garante no-op quando atividade nao-calibracao.
        register_predicate(
            "rt_competencia_cobre",
            rt_competencia_cobre,
            actions={
                "os.adicionar_atividade",
                "atividade.atribuir",
                "atividade.iniciar",
                "atividade.executar",
            },
        )

        # tenant_dentro_escopo_acreditado — STUB Wave A. Escopo
        # antecipa as actions que abrem atividade calibracao/inmetro.
        register_predicate(
            "tenant_dentro_escopo_acreditado",
            tenant_dentro_escopo_acreditado,
            actions={
                "os.adicionar_atividade",
                "atividade.iniciar",
            },
        )

        # pode_estender_janela_cal_link_atividade — 1 action exclusiva
        # (watchdog cal-link).
        register_predicate(
            "pode_estender_janela_cal_link_atividade",
            pode_estender_janela_cal_link_atividade,
            actions={"atividade.estender_janela_cal_link"},
        )

        # pode_dispensar_aceite — 1 action exclusiva.
        register_predicate(
            "pode_dispensar_aceite",
            pode_dispensar_aceite,
            actions={"atividade.dispensar_aceite"},
        )

        # pode_criar_os_produtiva_balancas — TODA `os.abrir`; predicate
        # self-guarda devolve True quando tenant != Balancas Solution.
        register_predicate(
            "pode_criar_os_produtiva_balancas",
            pode_criar_os_produtiva_balancas,
            actions={"os.abrir"},
        )
