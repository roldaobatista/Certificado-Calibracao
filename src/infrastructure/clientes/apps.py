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
