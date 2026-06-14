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
