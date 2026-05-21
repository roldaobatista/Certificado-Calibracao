"""Enum canonico de acoes de evento de dominio (BLOQ-A1 advogado).

Lista mantida em sincronia com o conjunto de eventos publicados via
`publicar_evento`. CHECK constraint do banco (`bus_outbox_acao_enum
_semantico`) garante o formato slug `dominio.entidade.op[.var]`; este
modulo garante o conjunto FECHADO de valores permitidos.

Cada modulo Wave A adiciona suas acoes com PR revisado pelo tech-lead
e auditor de seguranca. Manter ordenado por dominio.entidade.

Por que aqui (e nao no dominio): a tabela `bus_outbox` mora em F-A
(infrastructure/audit) — manter o enum aqui evita dependencia reversa
infrastructure -> domain.
"""

from __future__ import annotations

from typing import Final

# Marco 1 `clientes` — US-CLI-001..006.
ACOES_CLIENTES: Final[frozenset[str]] = frozenset(
    {
        "cliente.criado",
        "cliente.atualizado",
        "cliente.mesclado",
        "cliente.bloqueado",
        "cliente.desbloqueado",
        "cliente.importado_csv",
        "cliente.consentimento_revogado",
        "cliente.dados_eliminados",
        "cliente.dados_anonimizados",
        "cliente.dados_exportados",
        # T-CLI-119 (US-CLI-006 AC-006-6) — incidente PII (Res. ANPD 15/2024)
        "cliente.pii.incidente_detectado",
    }
)

# Eventos sistema (modo_sistema=1) — sem tenant_id.
ACOES_SISTEMA: Final[frozenset[str]] = frozenset(
    {
        "sistema.tenant_provisionado",
        "sistema.tenant_offboarded",
        "sistema.outbox_envenenado",
        # T-CLI-104 — circuit breaker observado AcessoDadosCliente
        "sistema.breaker_acesso_pii.disparado",
        "sistema.breaker_acesso_pii.normalizado",
    }
)

# Marco 2 `responsavel_tecnico` (US-EQP-007 / P-EQP-R10) — gestao do RT do tenant.
ACOES_RT: Final[frozenset[str]] = frozenset(
    {
        "tenant.rt.cadastrado",
        "tenant.rt.encerrado",
        "tenant.rt.trocado",
        "tenant.rt.competencia_declarada",
    }
)

ACOES_CANONICAS: Final[frozenset[str]] = ACOES_CLIENTES | ACOES_SISTEMA | ACOES_RT


def assert_acao_canonica(acao: str) -> None:
    """Helper pra chamador validar antes de `publicar_evento`.

    O banco tambem valida via CHECK; aqui eh fail-fast em camada Python
    (mensagem clara) — defesa em profundidade.
    """
    if acao not in ACOES_CANONICAS:
        raise ValueError(
            f"acao '{acao}' nao esta em acoes_canonicas.ACOES_CANONICAS. "
            "Cada acao nova exige PR + revisao do tech-lead + auditor de "
            "seguranca (BLOQ-A1 advogado)."
        )
