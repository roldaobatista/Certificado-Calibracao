from django.apps import AppConfig


class OrcamentosConfig(AppConfig):
    """Wave A — frente comercial/orcamentos (1a ponta de receita).

    Documento comercial que vira OS: carrinho de itens -> calculo (preco/
    desconto/imposto/comissao) -> envio com link de aprovacao -> aprovacao ->
    analise critica cl. 7.1 ISO 17025 -> publica `orcamento.aprovado` -> a OS
    (consumer ja pronto, ADR-0082) cria 1 OS com N atividades.

    Passo 1 da Saga 1 (ADR-0034). Spec: docs/faseamento/orcamentos/spec.md.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.orcamentos"
    label = "orcamentos"
    verbose_name = "Orcamentos (comercial)"

    def ready(self) -> None:
        """Registra consumers do bus (Onda 2d). Worker entra em run_in_tenant_context.

        - ``os.aberta`` -> ``handle_os_aberta`` fecha a saga (aprovado_pendente_os→
          convertido), publicando ``orcamento.convertido`` (T-ORC-035 / D-ORC-14).
        - ``cliente.dados_anonimizados`` -> ``handle_cliente_anonimizado`` cancela
          rascunhos / expira enviados do cliente (LGPD — T-ORC-036 / ADV-ORC-06).
        """
        from src.infrastructure.audit.outbox_worker import registrar_consumer

        from .consumers.cliente_anonimizado import handle_cliente_anonimizado
        from .consumers.os_aberta import handle_os_aberta

        _MAPA_CONSUMERS = {
            "os.aberta": handle_os_aberta,
            "cliente.dados_anonimizados": handle_cliente_anonimizado,
        }
        for acao, fn in _MAPA_CONSUMERS.items():
            try:
                registrar_consumer(acao, fn)
            except ValueError:
                # Já registrado (re-entry em test runner). Idempotente.
                pass
