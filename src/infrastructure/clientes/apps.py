from django.apps import AppConfig


class ClientesConfig(AppConfig):
    """Wave A · Marco 1 — modulo clientes.

    Comercial / clientes: entidade-base que praticamente todo outro
    modulo (OS, orcamentos, certificados, NFS-e, contas-receber) referencia.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.clientes"
    label = "clientes"
    verbose_name = "Clientes (comercial)"

    def ready(self) -> None:
        """Registra predicates ABAC + consumers do bus (US-CLI-004 / D-CR-11)."""
        from src.infrastructure.authz.predicates import register_predicate

        from .predicates_authz import cliente_nao_bloqueado

        # T-FB-01: escopo declarado — bloqueio comercial barra trabalho
        # OPERACIONAL sobre o cliente (OS/orçamento/agenda/chamado/
        # certificado). Gestão do próprio cadastro (`clientes.*`) e
        # financeiro (`fatura.*`) NÃO são barrados por bloqueio comercial
        # (decisão de produto registrada, revisável). O predicate ainda
        # se auto-guarda (resource sem `cliente_id` → não aplica).
        register_predicate(
            "cliente_nao_bloqueado",
            cliente_nao_bloqueado,
            actions={
                "os.",
                "orcamento.",
                "orcamentos.",
                "agenda.",
                "chamado.",
                "chamados.",
                "certificado.",
            },
        )

        # Fatia 3c (T-CR-045 / D-CR-11): consumer de `contas_receber.pago` →
        # desbloqueio do cliente quando a quitação zera a inadimplência vencida.
        # CR é dono do título e publica o fato; `clientes` é dono do bloqueio e
        # decide o desbloqueio (TL-CR-05 / R5).
        from src.infrastructure.audit.outbox_worker import registrar_consumer

        from .consumers.contas_receber_eventos import handle_contas_receber_pago

        try:
            registrar_consumer("contas_receber.pago", handle_contas_receber_pago)
        except ValueError:
            pass  # já registrado (re-entry do test runner / ready() chamado 2x)
