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

        # =============================================================
        # Fase 4 (P4 / T-OS-029..039) — consumers + sagas
        # Registra cada handler em audit.outbox_worker._REGISTRY por
        # nome de acao canonica. Worker `processar_outbox_em_contexto_tenant`
        # entra no `run_in_tenant_context(tenant_id)` antes de invocar.
        # =============================================================
        from src.infrastructure.audit.outbox_worker import registrar_consumer

        from .consumers.acreditacao import (
            handle_acreditacao_suspensa,
            handle_acreditacao_vencida,
        )
        from .consumers.calibracao import (
            handle_calibracao_concluida,
            handle_calibracao_iniciada,
        )
        from .consumers.cliente import handle_cliente_anonimizado
        from .consumers.equipamento import (
            handle_equipamento_baixado,
            handle_equipamento_descartado,
            handle_equipamento_recebimento_registrado,
        )
        from .consumers.financeiro import handle_os_faturada, handle_os_paga
        from .consumers.orcamento import handle_orcamento_aprovado
        from .consumers.tenant import handle_tenant_encerrado, handle_tenant_suspenso
        from .sagas.anonimizacao import handle_os_em_estado_terminal
        from .sagas.sucessao import handle_reabertura_solicitada
        from .sagas.sync_mobile import handle_sync_atividade, handle_sync_foto

        # Mapeamento de acao_canonica -> handler.
        # Acoes precisam estar no enum `acoes_canonicas.ACOES_CANONICAS`
        # (CHECK SQL bloqueia publish; consumer apenas escuta).
        _MAPA_CONSUMERS = {
            # T-OS-029
            "orcamento.aprovado": handle_orcamento_aprovado,
            # T-OS-030
            "cliente.anonimizado": handle_cliente_anonimizado,
            # T-OS-031
            "calibracao.iniciada": handle_calibracao_iniciada,
            "calibracao.concluida": handle_calibracao_concluida,
            # T-OS-032
            "os.faturada": handle_os_faturada,
            "os.paga": handle_os_paga,
            # T-OS-033
            "tenant.suspenso": handle_tenant_suspenso,
            "tenant.encerrado": handle_tenant_encerrado,
            # T-OS-034 + T-OS-036
            "equipamento.baixado": handle_equipamento_baixado,
            "equipamento.descartado": handle_equipamento_descartado,
            "equipamento_recebimento.registrado": handle_equipamento_recebimento_registrado,
            # T-OS-035
            "acreditacao.vencida": handle_acreditacao_vencida,
            "acreditacao.suspensa": handle_acreditacao_suspensa,
            # T-OS-037 saga anonimizacao — assina transicoes terminais de OS
            "os.concluida": handle_os_em_estado_terminal,
            "os.cancelada": handle_os_em_estado_terminal,
            # T-OS-038 saga sucessao
            "os.reabertura_solicitada": handle_reabertura_solicitada,
            # T-OS-039 saga sync mobile
            "sync.atividade_recebida": handle_sync_atividade,
            "sync.foto_recebida": handle_sync_foto,
        }
        for acao, fn in _MAPA_CONSUMERS.items():
            try:
                registrar_consumer(acao, fn)
            except ValueError:
                # Ja registrado (re-entry em test runner). Idempotente.
                pass
