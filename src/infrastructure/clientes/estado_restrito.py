"""T-CLI-106 (AC-CLI-003-7) — helpers de estado restrito do cliente.

Cliente importado com `aceite_lgpd_origem=IMPORTACAO_LEGADA` E
`pii_regularizacao_em IS NULL` está em ESTADO RESTRITO:
- **Sem campanhas marketing** — base CONSENTIMENTO não foi
  efetivamente capturada na importação legada.
- **Sem compartilhamento intermodular** — passa para o outbox
  com flag, módulos consumidores Wave A respeitam.
- Tenant regulariza via aceite formal posterior → seta
  `pii_regularizacao_em = now()` → estado restrito acaba.

Defesa adicional: `consentimento_revogado_em` também coloca cliente
em modo restrito pra finalidades que dependiam de CONSENTIMENTO
(T-CLI-115).
"""

from __future__ import annotations

from src.infrastructure.clientes.models import Cliente


def cliente_em_estado_restrito(cliente: Cliente) -> bool:
    """T-CLI-106 — True se cliente está em estado restrito.

    Casos:
    1. Importação legada não regularizada (`origem=IMPORTACAO_LEGADA`
       + `pii_regularizacao_em IS NULL`).
    2. Consentimento revogado E base atual é CONSENTIMENTO
       (T-CLI-115 — operações que dependiam dela ficam restritas).
    """
    if cliente.aceite_lgpd_origem == "IMPORTACAO_LEGADA" and cliente.pii_regularizacao_em is None:
        return True
    if (
        cliente.consentimento_revogado_em is not None
        and cliente.aceite_lgpd_base_legal == "CONSENTIMENTO"
    ):
        return True
    return False


def regularizar_aceite_legado(cliente: Cliente) -> Cliente:
    """T-CLI-106 — marca regularização do aceite legado.

    Use case: tenant captura aceite formal posterior à importação
    legada → seta `pii_regularizacao_em` → estado restrito acaba.
    Não muda `aceite_lgpd_origem` (mantém rastreabilidade da origem
    legada — auditoria de longo prazo).
    """
    from datetime import UTC, datetime

    if cliente.aceite_lgpd_origem != "IMPORTACAO_LEGADA":
        raise ValueError(
            f"regularizar_aceite_legado: cliente {cliente.id} não tem "
            f"origem=IMPORTACAO_LEGADA (atual: {cliente.aceite_lgpd_origem})"
        )
    if cliente.pii_regularizacao_em is not None:
        return cliente  # já regularizado — idempotente
    cliente.pii_regularizacao_em = datetime.now(UTC)
    cliente.save(update_fields=["pii_regularizacao_em", "atualizado_em"])
    return cliente
