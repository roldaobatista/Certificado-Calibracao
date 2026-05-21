"""App horizontal F-A: chave de idempotencia (T-EQP-003 / P-EQP-T6).

Tabela `idempotencia_chave` e infra COMPARTILHADA entre todos os endpoints
POST que precisam de protecao anti-replay (US-EQP-001 etiqueta + US-EQP-004
transferencia + US-EQP-002b aprovacao + US-EQP-005 sucatamento + US-EQP-006
recebimento + futuros). Por que app separada e nao em `equipamentos/`:

- Mais de um modulo consome (acoplar a `equipamentos` cria import circular
  quando `transferencia/` ou `comunicacao/` precisarem da mesma tabela).
- F-A horizontal: idempotencia e cross-cutting (junto com audit, multitenant,
  authz, feature_flag).
- Politica de retencao distinta (24h vs 25a do audit).

Spec: docs/arquitetura/cross-cutting/idempotencia.md
Plan: docs/faseamento/M2-equipamentos/plan.md P-EQP-T6
"""

from __future__ import annotations

from django.apps import AppConfig


class IdempotenciaConfig(AppConfig):
    """F-A horizontal — chave de idempotencia para POSTs criticos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.idempotencia"
    label = "idempotencia"
    verbose_name = "Idempotencia (F-A horizontal)"
