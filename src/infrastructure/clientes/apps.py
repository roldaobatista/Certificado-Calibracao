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
        """Registra predicates ABAC no AuthorizationProvider (US-CLI-004 TL2)."""
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
